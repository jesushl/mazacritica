import re
import unicodedata
from datetime import date
from pathlib import Path

from django.db import transaction

from .models import (
    Asentamiento,
    CodigoPostal,
    EmpalmePostalJudicial,
    Municipio,
    SepomexMunicipio,
)

SOURCE_POSTAL = 'CPdescarga.txt'
FUENTE_JUDICIAL = 'SECCION_CIRCUITO_DISTRITOJUDICIAL_10FEB25.xlsx'
CRITERIO = 'nombre_en_entidad'
VIGENCIA = date(2025, 2, 10)
BATCH = 2000


def load_codigos_postales(data_dir):
    path = Path(data_dir) / SOURCE_POSTAL
    municipios, codigos = _leer(path)
    cruces = _cruces_seguros()

    with transaction.atomic():
        Asentamiento.objects.all().delete()
        CodigoPostal.objects.all().delete()
        SepomexMunicipio.objects.all().delete()

        sepomex_rows = [
            SepomexMunicipio(
                c_estado=c_estado,
                c_mnpio=c_mnpio,
                nombre=datos['nombre'],
                nombre_estado=datos['nombre_estado'],
                municipio_id=_municipio_seguro(cruces, c_estado, c_mnpio, datos['nombre']),
            )
            for (c_estado, c_mnpio), datos in municipios.items()
        ]
        SepomexMunicipio.objects.bulk_create(sepomex_rows, batch_size=BATCH)
        sepomex_ids = {
            (item.c_estado, item.c_mnpio): item.id
            for item in SepomexMunicipio.objects.all()
        }

        postal_rows = [
            CodigoPostal(
                codigo=codigo,
                municipio_id=sepomex_ids[datos['municipio']],
            )
            for codigo, datos in codigos.items()
        ]
        for offset in range(0, len(postal_rows), BATCH):
            CodigoPostal.objects.bulk_create(postal_rows[offset:offset + BATCH], batch_size=BATCH)
        postal_ids = {item.codigo: item.id for item in CodigoPostal.objects.all()}

        asentamientos = []
        for codigo, datos in codigos.items():
            postal_id = postal_ids[codigo]
            for asentamiento in datos['asentamientos'].values():
                asentamientos.append(Asentamiento(
                    codigo_id=postal_id,
                    clave=asentamiento['clave'],
                    nombre=asentamiento['nombre'],
                    tipo=asentamiento['tipo'],
                ))
        for offset in range(0, len(asentamientos), BATCH):
            Asentamiento.objects.bulk_create(
                asentamientos[offset:offset + BATCH],
                batch_size=BATCH,
            )

        EmpalmePostalJudicial.objects.update_or_create(
            criterio=CRITERIO,
            defaults={
                'vigencia': VIGENCIA,
                'fuente_postal': SOURCE_POSTAL,
                'fuente_judicial': FUENTE_JUDICIAL,
            },
        )

    return {
        'municipios': len(municipios),
        'codigos': len(codigos),
        'asentamientos': Asentamiento.objects.count(),
    }


def normalizar_nombre(value):
    text = unicodedata.normalize('NFD', value or '')
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
    text = text.upper()
    for particle in (' DE LOS ', ' DE LAS ', ' DE LA ', ' DEL ', ' DE '):
        text = text.replace(particle, ' ')
    text = re.sub(r'[^A-Z0-9 ]', '', text)
    return re.sub(r'\s+', '', text)


def _municipio_seguro(cruces, c_estado, c_mnpio, nombre):
    candidatos = cruces.get((c_estado, normalizar_nombre(nombre)), [])
    if len(candidatos) != 1:
        return None
    return candidatos[0].id


def _cruces_seguros():
    grupos = {}
    for item in Municipio.objects.select_related('entidad'):
        grupos.setdefault((item.entidad.clave, normalizar_nombre(item.nombre)), []).append(item)
    return grupos


def _leer(path):
    municipios = {}
    codigos = {}
    with path.open(encoding='latin-1') as handle:
        handle.readline()
        header = handle.readline().rstrip('\r\n').split('|')
        for line in handle:
            parts = line.rstrip('\r\n').split('|')
            if len(parts) != len(header):
                continue
            row = dict(zip(header, parts))
            codigo = row['d_codigo'].strip().zfill(5)
            if not codigo.isdigit() or len(codigo) != 5:
                continue
            c_estado = int(row['c_estado'].strip())
            c_mnpio = int(row['c_mnpio'].strip())
            nombre = row['D_mnpio'].strip()
            nombre_estado = row['d_estado'].strip()
            actual = municipios.get((c_estado, c_mnpio))
            if actual is None:
                municipios[(c_estado, c_mnpio)] = {
                    'nombre': nombre,
                    'nombre_estado': nombre_estado,
                }
            clave = row['id_asenta_cpcons'].strip()
            postal = codigos.get(codigo)
            if postal is None:
                postal = {
                    'municipio': (c_estado, c_mnpio),
                    'asentamientos': {},
                }
                codigos[codigo] = postal
            elif postal['municipio'] != (c_estado, c_mnpio):
                continue
            postal['asentamientos'][clave] = {
                'clave': clave,
                'nombre': row['d_asenta'].strip(),
                'tipo': row['d_tipo_asenta'].strip(),
            }
    return municipios, codigos
