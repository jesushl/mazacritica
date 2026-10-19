import zipfile
from datetime import date
from html import escape
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import TestCase

from api.models import PostalCode, PostalCodeZoneMapping

from .geoelectoral import SOURCE_GEO, SOURCE_SECCIONES, VIGENCIA_JUDICIAL
from .models import (
    AsignacionDistritoJudicial,
    ManzanaGeoelectoral,
    SeccionElectoral,
)
from .regiones import regiones_de_municipio


class GeoelectoralLoadTests(TestCase):
    def test_empalma_secciones_y_lista_las_regiones_sin_elegir_una(self):
        postales = PostalCode.objects.count()
        mapeos = PostalCodeZoneMapping.objects.count()
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _xlsx(root / 'Catálogo de Distritos.xlsx', [
                ['ENTIDAD', 'NOMBRE ENTIDAD', 'DISTRITO'],
                ['1', 'AGUASCALIENTES', '1'],
                ['1', 'AGUASCALIENTES', '2'],
            ])
            municipio = [
                'ENTIDAD', 'NOMBRE DE ENTIDAD', 'CIRCUITO JUDICIAL', 'ROMANO',
                'NOMBRE DE CIRCUITO JUDICIAL', 'DISTRITO FEDERAL ELECTORAL',
                'DISTRITO JUDICIAL ELECTORAL', 'MUNICIPIO', 'NOMBRE DE MUNICIPIO',
            ]
            _xlsx(root / 'MUNICIPIO_CIRCUITO_DISTRITOJUDICIAL_10FEB25.xlsx', [
                municipio,
                ['1', 'AGUASCALIENTES', '30', 'XXX', 'ESTADO DE AGUASCALIENTES', '1', '9', '2', 'ASIENTOS'],
                ['1', 'AGUASCALIENTES', '30', 'XXX', 'ESTADO DE AGUASCALIENTES', '2', '2', '2', 'ASIENTOS'],
            ])
            _xlsx(root / 'SECCION_CIRCUITO_DISTRITOJUDICIAL_10FEB25.xlsx', [
                municipio + ['SECCION'],
                ['1', 'AGUASCALIENTES', '30', 'XXX', 'ESTADO DE AGUASCALIENTES', '1', '9', '2', 'ASIENTOS', '338'],
                ['1', 'AGUASCALIENTES', '30', 'XXX', 'ESTADO DE AGUASCALIENTES', '2', '2', '2', 'ASIENTOS', '339'],
                ['1', 'AGUASCALIENTES', '30', 'XXX', 'ESTADO DE AGUASCALIENTES', '1', '9', '2', 'ASIENTOS', '400'],
            ])
            (root / 'Catalogodeinformaciongeoelectoral(EDMSLM).txt').write_text(
                'ENTIDAD|DISTRITO|MUNICIPIO|NOMBRE_MUNICIPIO|SECCION|TIPO_SECCION|TIPO_NOMBRE|'
                'LOCALIDAD|NOMBRE_LOCALIDAD|TIPO_LOCALIDAD|TIPO_NOMBRE_LOCALIDAD|MANZANA|STATUS\n'
                '1|1|2|ASIENTOS|338|3|MIXTO(A)|1|ASIENTOS|2|URBANO(A)|1|C\n'
                '1|1|2|ASIENTOS|338|3|MIXTO(A)|1|ASIENTOS|2|URBANO(A)|2|*\n'
                '1|1|2|ASIENTOS|500|1|URBANO(A)|1|ASIENTOS|2|URBANO(A)|3|C\n',
                encoding='utf-8',
            )
            call_command('load_geoelectoral', data_dir=str(root))
            call_command('load_geoelectoral', data_dir=str(root))

        compartida = SeccionElectoral.objects.get(numero=338)
        self.assertEqual(compartida.distrito_federal.numero, 1)
        self.assertEqual(compartida.tipo_nombre, 'MIXTO(A)')
        self.assertEqual(compartida.fuente, SOURCE_GEO)
        asignacion = compartida.asignacion_judicial
        self.assertEqual(asignacion.distrito_judicial.numero, 9)
        self.assertEqual(asignacion.vigencia, VIGENCIA_JUDICIAL)
        self.assertEqual(asignacion.fuente, SOURCE_SECCIONES)
        self.assertNotEqual(
            compartida.distrito_federal.numero,
            asignacion.distrito_judicial.numero,
        )

        solo_corte = SeccionElectoral.objects.get(numero=400)
        self.assertEqual(solo_corte.fuente, SOURCE_SECCIONES)
        self.assertTrue(AsignacionDistritoJudicial.objects.filter(seccion=solo_corte).exists())

        solo_catalogo = SeccionElectoral.objects.get(numero=500)
        self.assertEqual(solo_catalogo.fuente, SOURCE_GEO)
        self.assertFalse(
            AsignacionDistritoJudicial.objects.filter(seccion=solo_catalogo).exists()
        )

        self.assertEqual(SeccionElectoral.objects.count(), 4)
        self.assertEqual(ManzanaGeoelectoral.objects.count(), 3)
        self.assertCountEqual(
            [item.status for item in ManzanaGeoelectoral.objects.filter(seccion__numero=338)],
            ['C', '*'],
        )

        regiones = regiones_de_municipio(1, 2)
        self.assertEqual([region['numero'] for region in regiones], [2, 9])
        self.assertEqual([region['secciones'] for region in regiones], [1, 2])
        self.assertTrue(all('ganador' not in region for region in regiones))
        self.assertEqual(regiones[0]['circuito']['romano'], 'XXX')
        self.assertEqual(regiones[0]['circuito']['nombre'], 'ESTADO DE AGUASCALIENTES')
        self.assertEqual(asignacion.vigencia, date(2025, 2, 10))

        self.assertEqual(PostalCode.objects.count(), postales)
        self.assertEqual(PostalCodeZoneMapping.objects.count(), mapeos)


def _xlsx(path, rows):
    sheet_rows = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for column_index, value in enumerate(row, start=1):
            ref = f'{_column_name(column_index)}{row_index}'
            cells.append(
                f'<c r="{ref}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>'
            )
        sheet_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    worksheet = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(sheet_rows)}</sheetData></worksheet>'
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="1" sheetId="1" r:id="rId1"/></sheets></workbook>'
    )
    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        'Target="worksheets/sheet1.xml"/>'
        '</Relationships>'
    )
    package_rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/>'
        '</Relationships>'
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '</Types>'
    )
    with zipfile.ZipFile(path, 'w') as book:
        book.writestr('[Content_Types].xml', content_types)
        book.writestr('_rels/.rels', package_rels)
        book.writestr('xl/workbook.xml', workbook)
        book.writestr('xl/_rels/workbook.xml.rels', workbook_rels)
        book.writestr('xl/worksheets/sheet1.xml', worksheet)


def _column_name(number):
    name = ''
    while number:
        number, remainder = divmod(number - 1, 26)
        name = chr(65 + remainder) + name
    return name
