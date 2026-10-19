import zipfile
from datetime import date
from pathlib import Path
from xml.etree import ElementTree as ET

from django.db import transaction

from .models import (
    AsignacionDistritoJudicial,
    CircuitoJudicial,
    DistritoFederalElectoral,
    DistritoJudicialElectoral,
    Entidad,
    Localidad,
    ManzanaGeoelectoral,
    Municipio,
    SeccionElectoral,
)

SOURCE_DISTRICTS = 'Catálogo de Distritos.xlsx'
SOURCE_MUNICIPIOS = 'MUNICIPIO_CIRCUITO_DISTRITOJUDICIAL_10FEB25.xlsx'
SOURCE_SECCIONES = 'SECCION_CIRCUITO_DISTRITOJUDICIAL_10FEB25.xlsx'
SOURCE_GEO = 'Catalogodeinformaciongeoelectoral(EDMSLM).txt'
VIGENCIA_JUDICIAL = date(2025, 2, 10)
BATCH = 2000

NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def load_geoelectoral(data_dir):
    data_dir = Path(data_dir)
    catalogo = _rows(data_dir / SOURCE_DISTRICTS)
    municipios = _rows(data_dir / SOURCE_MUNICIPIOS)
    secciones = _rows(data_dir / SOURCE_SECCIONES)
    geo_path = data_dir / SOURCE_GEO

    entidades = {}
    federales = {}
    circuitos = {}
    judiciales = {}
    municipios_catalogo = {}
    secciones_catalogo = {}
    asignaciones = {}
    localidades = {}

    _take_distritos(catalogo, entidades, federales)
    _take_municipios(municipios, entidades, federales, circuitos, judiciales, municipios_catalogo)
    _take_secciones(
        secciones,
        entidades,
        federales,
        circuitos,
        judiciales,
        municipios_catalogo,
        secciones_catalogo,
        asignaciones,
    )
    _take_geo_padres(
        geo_path,
        entidades,
        federales,
        municipios_catalogo,
        secciones_catalogo,
        localidades,
    )

    with transaction.atomic():
        entidad_ids = _upsert_entidades(entidades)
        federal_ids = _upsert_federales(federales, entidad_ids)
        circuito_ids = _upsert_circuitos(circuitos, entidad_ids)
        judicial_ids = _upsert_judiciales(judiciales, entidad_ids)
        municipio_ids = _upsert_municipios(municipios_catalogo, entidad_ids)
        seccion_ids = _upsert_secciones(
            secciones_catalogo,
            entidad_ids,
            municipio_ids,
            federal_ids,
        )
        _upsert_asignaciones(asignaciones, seccion_ids, judicial_ids, circuito_ids)
        localidad_ids = _upsert_localidades(localidades, municipio_ids)
        manzanas = _cargar_manzanas(geo_path, seccion_ids, localidad_ids, municipio_ids)

    return {
        'entidades': len(entidad_ids),
        'distritos_federales': len(federal_ids),
        'circuitos': len(circuito_ids),
        'distritos_judiciales': len(judicial_ids),
        'municipios': len(municipio_ids),
        'secciones': len(seccion_ids),
        'asignaciones': len(asignaciones),
        'localidades': len(localidad_ids),
        'manzanas': manzanas,
    }


def _take_distritos(rows, entidades, federales):
    for row in rows:
        clave = _entero(row['ENTIDAD'])
        _note_entidad(entidades, clave, row['NOMBRE ENTIDAD'], SOURCE_DISTRICTS)
        federales[(clave, _entero(row['DISTRITO']))] = SOURCE_DISTRICTS


def _take_municipios(rows, entidades, federales, circuitos, judiciales, municipios):
    for row in rows:
        clave = _entero(row['ENTIDAD'])
        _note_entidad(entidades, clave, row['NOMBRE DE ENTIDAD'], SOURCE_MUNICIPIOS)
        federales.setdefault((clave, _entero(row['DISTRITO FEDERAL ELECTORAL'])), SOURCE_MUNICIPIOS)
        judiciales.setdefault((clave, _entero(row['DISTRITO JUDICIAL ELECTORAL'])), SOURCE_MUNICIPIOS)
        circuitos.setdefault(clave, {
            'numero': _entero(row['CIRCUITO JUDICIAL']),
            'romano': row['ROMANO'].strip(),
            'nombre': row['NOMBRE DE CIRCUITO JUDICIAL'].strip(),
            'fuente': SOURCE_MUNICIPIOS,
        })
        _note_municipio(
            municipios,
            clave,
            _entero(row['MUNICIPIO']),
            row['NOMBRE DE MUNICIPIO'],
            SOURCE_MUNICIPIOS,
        )


def _take_secciones(
    rows,
    entidades,
    federales,
    circuitos,
    judiciales,
    municipios,
    secciones,
    asignaciones,
):
    for row in rows:
        clave = _entero(row['ENTIDAD'])
        numero = _entero(row['SECCION'])
        federal = _entero(row['DISTRITO FEDERAL ELECTORAL'])
        _note_entidad(entidades, clave, row['NOMBRE DE ENTIDAD'], SOURCE_SECCIONES)
        federales.setdefault((clave, federal), SOURCE_SECCIONES)
        judiciales.setdefault((clave, _entero(row['DISTRITO JUDICIAL ELECTORAL'])), SOURCE_SECCIONES)
        circuitos.setdefault(clave, {
            'numero': _entero(row['CIRCUITO JUDICIAL']),
            'romano': row['ROMANO'].strip(),
            'nombre': row['NOMBRE DE CIRCUITO JUDICIAL'].strip(),
            'fuente': SOURCE_SECCIONES,
        })
        municipio = _entero(row['MUNICIPIO'])
        _note_municipio(municipios, clave, municipio, row['NOMBRE DE MUNICIPIO'], SOURCE_SECCIONES)
        current = secciones.get((clave, numero))
        if current is None or not current['desde_geo']:
            secciones[(clave, numero)] = {
                'municipio': municipio,
                'tipo': '',
                'tipo_nombre': '',
                'distrito_federal': federal,
                'fuente': SOURCE_SECCIONES,
                'desde_geo': False,
            }
        asignaciones[(clave, numero)] = {
            'judicial': _entero(row['DISTRITO JUDICIAL ELECTORAL']),
            'fuente': SOURCE_SECCIONES,
        }


def _take_geo_padres(path, entidades, federales, municipios, secciones, localidades):
    for row in _geo_rows(path):
        clave = _entero(row['ENTIDAD'])
        municipio = _entero(row['MUNICIPIO'])
        seccion = _entero(row['SECCION'])
        federal = _entero(row['DISTRITO'])
        _note_entidad(entidades, clave, '', SOURCE_GEO)
        federales.setdefault((clave, federal), SOURCE_GEO)
        _note_municipio(municipios, clave, municipio, row['NOMBRE_MUNICIPIO'], SOURCE_GEO)
        secciones[(clave, seccion)] = {
            'municipio': municipio,
            'tipo': row['TIPO_SECCION'].strip(),
            'tipo_nombre': row['TIPO_NOMBRE'].strip(),
            'distrito_federal': federal,
            'fuente': SOURCE_GEO,
            'desde_geo': True,
        }
        localidades[(clave, municipio, _entero(row['LOCALIDAD']))] = {
            'nombre': row['NOMBRE_LOCALIDAD'].strip(),
            'tipo': row['TIPO_LOCALIDAD'].strip(),
            'tipo_nombre': row['TIPO_NOMBRE_LOCALIDAD'].strip(),
            'fuente': SOURCE_GEO,
        }


def _cargar_manzanas(path, seccion_ids, localidad_ids, municipio_ids):
    total = 0
    pending = {}
    for row in _geo_rows(path):
        entidad = _entero(row['ENTIDAD'])
        municipio = _entero(row['MUNICIPIO'])
        seccion = seccion_ids[(entidad, _entero(row['SECCION']))]
        localidad = localidad_ids[(municipio_ids[(entidad, municipio)], _entero(row['LOCALIDAD']))]
        clave = row['MANZANA'].strip()
        pending[(seccion, localidad, clave)] = ManzanaGeoelectoral(
            seccion_id=seccion,
            localidad_id=localidad,
            clave=clave,
            status=row['STATUS'].strip(),
            fuente=SOURCE_GEO,
        )
        if len(pending) >= BATCH:
            total += _flush_manzanas(list(pending.values()))
            pending = {}
    if pending:
        total += _flush_manzanas(list(pending.values()))
    return total


def _flush_manzanas(batch):
    ManzanaGeoelectoral.objects.bulk_create(
        batch,
        batch_size=BATCH,
        update_conflicts=True,
        unique_fields=['seccion', 'localidad', 'clave'],
        update_fields=['status', 'fuente'],
    )
    return len(batch)


def _upsert_entidades(entidades):
    Entidad.objects.bulk_create(
        [
            Entidad(clave=clave, nombre=datos['nombre'], fuente=datos['fuente'])
            for clave, datos in entidades.items()
        ],
        update_conflicts=True,
        unique_fields=['clave'],
        update_fields=['nombre', 'fuente'],
        batch_size=BATCH,
    )
    return {item.clave: item.id for item in Entidad.objects.all()}


def _upsert_federales(federales, entidad_ids):
    DistritoFederalElectoral.objects.bulk_create(
        [
            DistritoFederalElectoral(
                entidad_id=entidad_ids[entidad],
                numero=numero,
                fuente=fuente,
            )
            for (entidad, numero), fuente in federales.items()
        ],
        update_conflicts=True,
        unique_fields=['entidad', 'numero'],
        update_fields=['fuente'],
        batch_size=BATCH,
    )
    return {
        (item.entidad.clave, item.numero): item.id
        for item in DistritoFederalElectoral.objects.select_related('entidad')
    }


def _upsert_circuitos(circuitos, entidad_ids):
    CircuitoJudicial.objects.bulk_create(
        [
            CircuitoJudicial(
                entidad_id=entidad_ids[entidad],
                numero=datos['numero'],
                romano=datos['romano'],
                nombre=datos['nombre'],
                fuente=datos['fuente'],
            )
            for entidad, datos in circuitos.items()
        ],
        update_conflicts=True,
        unique_fields=['entidad'],
        update_fields=['numero', 'romano', 'nombre', 'fuente'],
        batch_size=BATCH,
    )
    return {
        item.entidad.clave: item.id
        for item in CircuitoJudicial.objects.select_related('entidad')
    }


def _upsert_judiciales(judiciales, entidad_ids):
    DistritoJudicialElectoral.objects.bulk_create(
        [
            DistritoJudicialElectoral(
                entidad_id=entidad_ids[entidad],
                numero=numero,
                fuente=fuente,
            )
            for (entidad, numero), fuente in judiciales.items()
        ],
        update_conflicts=True,
        unique_fields=['entidad', 'numero'],
        update_fields=['fuente'],
        batch_size=BATCH,
    )
    return {
        (item.entidad.clave, item.numero): item.id
        for item in DistritoJudicialElectoral.objects.select_related('entidad')
    }


def _upsert_municipios(municipios, entidad_ids):
    Municipio.objects.bulk_create(
        [
            Municipio(
                entidad_id=entidad_ids[entidad],
                clave=clave,
                nombre=datos['nombre'],
                fuente=datos['fuente'],
            )
            for (entidad, clave), datos in municipios.items()
        ],
        update_conflicts=True,
        unique_fields=['entidad', 'clave'],
        update_fields=['nombre', 'fuente'],
        batch_size=BATCH,
    )
    return {
        (item.entidad.clave, item.clave): item.id
        for item in Municipio.objects.select_related('entidad')
    }


def _upsert_secciones(secciones, entidad_ids, municipio_ids, federal_ids):
    SeccionElectoral.objects.bulk_create(
        [
            SeccionElectoral(
                entidad_id=entidad_ids[entidad],
                municipio_id=municipio_ids[(entidad, datos['municipio'])],
                numero=numero,
                tipo=datos['tipo'],
                tipo_nombre=datos['tipo_nombre'],
                distrito_federal_id=federal_ids.get((entidad, datos['distrito_federal'])),
                fuente=datos['fuente'],
            )
            for (entidad, numero), datos in secciones.items()
        ],
        update_conflicts=True,
        unique_fields=['entidad', 'numero'],
        update_fields=['municipio', 'tipo', 'tipo_nombre', 'distrito_federal', 'fuente'],
        batch_size=BATCH,
    )
    return {
        (item.entidad.clave, item.numero): item.id
        for item in SeccionElectoral.objects.select_related('entidad')
    }


def _upsert_asignaciones(asignaciones, seccion_ids, judicial_ids, circuito_ids):
    AsignacionDistritoJudicial.objects.bulk_create(
        [
            AsignacionDistritoJudicial(
                seccion_id=seccion_ids[(entidad, numero)],
                distrito_judicial_id=judicial_ids[(entidad, datos['judicial'])],
                circuito_id=circuito_ids[entidad],
                fuente=datos['fuente'],
                vigencia=VIGENCIA_JUDICIAL,
            )
            for (entidad, numero), datos in asignaciones.items()
        ],
        update_conflicts=True,
        unique_fields=['seccion'],
        update_fields=['distrito_judicial', 'circuito', 'fuente', 'vigencia'],
        batch_size=BATCH,
    )


def _upsert_localidades(localidades, municipio_ids):
    Localidad.objects.bulk_create(
        [
            Localidad(
                municipio_id=municipio_ids[(entidad, municipio)],
                clave=clave,
                nombre=datos['nombre'],
                tipo=datos['tipo'],
                tipo_nombre=datos['tipo_nombre'],
                fuente=datos['fuente'],
            )
            for (entidad, municipio, clave), datos in localidades.items()
        ],
        update_conflicts=True,
        unique_fields=['municipio', 'clave'],
        update_fields=['nombre', 'tipo', 'tipo_nombre', 'fuente'],
        batch_size=BATCH,
    )
    return {
        (item.municipio_id, item.clave): item.id
        for item in Localidad.objects.all()
    }


def _note_entidad(entidades, clave, nombre, fuente):
    nombre = (nombre or '').strip()
    current = entidades.get(clave)
    if current is None:
        entidades[clave] = {'nombre': nombre, 'fuente': fuente}
    elif nombre and (not current['nombre'] or fuente == SOURCE_DISTRICTS):
        current['nombre'] = nombre
        current['fuente'] = fuente


def _note_municipio(municipios, entidad, clave, nombre, fuente):
    nombre = (nombre or '').strip()
    current = municipios.get((entidad, clave))
    if current is None or (nombre and not current['nombre']):
        municipios[(entidad, clave)] = {'nombre': nombre, 'fuente': fuente}


def _entero(value):
    text = str(value).strip()
    if text.isdigit():
        return int(text)
    return int(float(text))


def _rows(path):
    header, data = _xlsx_rows(path)
    return [dict(zip(header, row)) for row in data]


def _xlsx_rows(path):
    with zipfile.ZipFile(path) as book:
        shared = []
        if 'xl/sharedStrings.xml' in book.namelist():
            root = ET.fromstring(book.read('xl/sharedStrings.xml'))
            shared = [
                ''.join(node.text or '' for node in item.iter(_q('t')))
                for item in root.findall('m:si', NS)
            ]
        sheet_name = next(name for name in book.namelist() if name.startswith('xl/worksheets/sheet'))
        root = ET.fromstring(book.read(sheet_name))
    rows = []
    for row in root.findall('m:sheetData/m:row', NS):
        values = {}
        for cell in row.findall('m:c', NS):
            raw = cell.find('m:v', NS)
            inline = cell.find('m:is/m:t', NS)
            if raw is not None and raw.text is not None:
                value = shared[int(raw.text)] if cell.attrib.get('t') == 's' else raw.text
            elif inline is not None:
                value = inline.text or ''
            else:
                continue
            values[_column(cell.attrib.get('r', ''))] = value
        if values:
            width = max(values) + 1
            rows.append([values.get(index, '') for index in range(width)])
    if not rows:
        return [], []
    return rows[0], rows[1:]


def _geo_rows(path):
    with path.open(encoding='utf-8', errors='replace') as handle:
        header = handle.readline().lstrip('\ufeff').rstrip('\n').split('|')
        for line in handle:
            parts = line.rstrip('\n').split('|')
            if len(parts) != len(header):
                continue
            yield dict(zip(header, parts))


def _column(ref):
    letters = ''.join(char for char in ref if char.isalpha())
    number = 0
    for char in letters:
        number = number * 26 + ord(char) - 64
    return number - 1


def _q(name):
    return f'{{{NS["m"]}}}{name}'
