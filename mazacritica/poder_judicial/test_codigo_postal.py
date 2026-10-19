from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from api.models import ElectionZone, PostalCode, PostalCodeZoneMapping

from .models import (
    Asentamiento,
    AsignacionDistritoJudicial,
    CircuitoJudicial,
    CodigoPostal,
    DistritoJudicialElectoral,
    Entidad,
    Municipio,
    SeccionElectoral,
    SepomexMunicipio,
)
from .regiones import buscar_codigo_postal

FUENTE = 'prueba'
VIGENCIA = date(2025, 2, 10)
AVISO = (
    'El Catálogo Nacional de Códigos Postales, es elaborado por Correos de México '
    'y se proporciona en forma gratuita para uso particular.\n'
)
ENCABEZADO = (
    'd_codigo|d_asenta|d_tipo_asenta|D_mnpio|d_estado|d_ciudad|d_CP|'
    'c_estado|c_oficina|c_CP|c_tipo_asenta|c_mnpio|id_asenta_cpcons|d_zona|c_cve_ciudad\n'
)


class CodigoPostalJudicialTests(TestCase):
    def test_cruza_por_clave_y_nombre_sin_elegir_distrito(self):
        zona = ElectionZone.objects.create(name='Zona de control', code='ZZ-CONTROL')
        postal = PostalCode.objects.create(code='99001')
        PostalCodeZoneMapping.objects.create(
            postal_code=postal,
            zone=zona,
            source='Control de la carga',
            valid_from=date(2024, 1, 1),
            valid_to=date(2027, 12, 31),
        )
        postales = PostalCode.objects.count()
        mapeos = PostalCodeZoneMapping.objects.count()
        _catalogo_judicial()
        secciones = SeccionElectoral.objects.count()
        asignaciones = AsignacionDistritoJudicial.objects.count()

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'CPdescarga.txt').write_text(_catalogo_postal(), encoding='latin-1')
            call_command('load_codigos_postales', data_dir=str(root))
            codigos = CodigoPostal.objects.count()
            asentamientos = Asentamiento.objects.count()
            municipios = SepomexMunicipio.objects.count()
            call_command('load_codigos_postales', data_dir=str(root))

        self.assertEqual(CodigoPostal.objects.count(), codigos)
        self.assertEqual(Asentamiento.objects.count(), asentamientos)
        self.assertEqual(SepomexMunicipio.objects.count(), municipios)
        self.assertEqual(SeccionElectoral.objects.count(), secciones)
        self.assertEqual(AsignacionDistritoJudicial.objects.count(), asignaciones)
        self.assertEqual(PostalCode.objects.count(), postales)
        self.assertEqual(PostalCodeZoneMapping.objects.count(), mapeos)

        paz = buscar_codigo_postal('23000')
        self.assertEqual(paz['codigo'], '23000')
        self.assertEqual(paz['municipio_sepomex']['c_estado'], 3)
        self.assertEqual(paz['municipio_sepomex']['c_mnpio'], 3)
        self.assertEqual(paz['municipio_sepomex']['nombre'], 'LA PAZ')
        self.assertEqual(paz['municipio'], {'clave': 3, 'nombre': 'LA PAZ', 'entidad': 3})
        self.assertEqual(paz['criterio'], 'nombre_en_entidad')
        self.assertEqual(paz['vigencia'], '2025-02-10')
        self.assertEqual(len(paz['distritos']), 1)
        self.assertEqual(paz['distritos'][0]['numero'], 1)
        self.assertEqual(paz['distritos'][0]['secciones'], 2)
        self.assertEqual(paz['asentamientos'], [{'nombre': 'Centro', 'tipo': 'Colonia'}])
        self.assertNotIn('ganador', paz)
        self.assertNotIn('elegido', paz)

        torreon = buscar_codigo_postal('27000')
        self.assertEqual(
            [(item['numero'], item['secciones']) for item in torreon['distritos']],
            [(1, 2), (2, 1)],
        )
        self.assertEqual(
            {item['circuito']['numero'] for item in torreon['distritos']},
            {torreon['distritos'][0]['circuito']['numero']},
        )
        self.assertTrue(all('ganador' not in item and 'elegido' not in item for item in torreon['distritos']))
        self.assertEqual(torreon['municipio']['clave'], 35)
        self.assertEqual(torreon['municipio']['entidad'], 5)

        cabos = buscar_codigo_postal('23400')
        self.assertEqual(cabos['municipio'], {'clave': 9, 'nombre': 'LOS CABOS', 'entidad': 3})
        self.assertEqual(
            [(item['numero'], item['secciones']) for item in cabos['distritos']],
            [(1, 1)],
        )

        loreto = buscar_codigo_postal('23880')
        self.assertIsNone(loreto['municipio'])
        self.assertEqual(loreto['distritos'], [])

        otro = buscar_codigo_postal('44100')
        self.assertIsNone(otro['municipio'])
        self.assertEqual(otro['distritos'], [])
        self.assertEqual(otro['municipio_sepomex']['nombre'], 'OTRO LUGAR')

        self.assertIsNone(buscar_codigo_postal('00000'))

        response = APIClient().get('/poder-judicial/distrito/?code=27000')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [zone['code'] for zone in response.data['zones']],
            ['DJ-5-1', 'DJ-5-2'],
        )
        self.assertEqual(response.data['municipio'], 'TORREON')
        self.assertEqual(response.data['aspirantes'], [])
        empty = APIClient().get('/poder-judicial/distrito/?code=23880')
        self.assertEqual(empty.data['zones'], [])
        self.assertIn('catálogo postal', empty.data['detail'])


def _catalogo_judicial():
    baja = _entidad(3, 'BAJA CALIFORNIA SUR')
    coahuila = _entidad(5, 'COAHUILA')
    jalisco = _entidad(14, 'JALISCO')
    zacatecas = _entidad(32, 'ZACATECAS')
    _municipio(zacatecas, 24, 'LORETO')
    circuito_baja = _circuito(baja, 3, 'III', 'CIRCUITO DE BAJA CALIFORNIA SUR')
    circuito_coahuila = _circuito(coahuila, 8, 'VIII', 'CIRCUITO DE COAHUILA')
    circuito_jalisco = _circuito(jalisco, 4, 'IV', 'CIRCUITO DE JALISCO')

    la_paz = _municipio(baja, 3, 'LA PAZ')
    _municipio(baja, 9, 'LOS CABOS')
    torreon = _municipio(coahuila, 35, 'TORREON')
    guadalajara = _municipio(jalisco, 41, 'GUADALAJARA')

    distrito_paz = _distrito(baja, 1)
    distrito_torreon_1 = _distrito(coahuila, 1)
    distrito_torreon_2 = _distrito(coahuila, 2)
    distrito_gdl = _distrito(jalisco, 1)

    _seccion(baja, la_paz, 1, distrito_paz, circuito_baja)
    _seccion(baja, la_paz, 2, distrito_paz, circuito_baja)
    _seccion(coahuila, torreon, 10, distrito_torreon_1, circuito_coahuila)
    _seccion(coahuila, torreon, 11, distrito_torreon_1, circuito_coahuila)
    _seccion(coahuila, torreon, 12, distrito_torreon_2, circuito_coahuila)
    _seccion(jalisco, guadalajara, 20, distrito_gdl, circuito_jalisco)
    _seccion(baja, Municipio.objects.get(entidad=baja, clave=9), 30, distrito_paz, circuito_baja)


def _catalogo_postal():
    filas = [
        '23000|Centro|Colonia|LA PAZ|Baja California Sur|||03||||003|0001||',
        '27000|Centro|Colonia|TORREON|Coahuila de Zaragoza|||05||||035|0001||',
        '23400|Centro|Colonia|LOS CABOS|Baja California Sur|||03||||008|0001||',
        '23880|Centro|Colonia|LORETO|Baja California Sur|||03||||009|0001||',
        '44100|Centro|Colonia|OTRO LUGAR|Jalisco|||14||||041|0001||',
    ]
    return AVISO + ENCABEZADO + '\n'.join(filas) + '\n'


def _entidad(clave, nombre):
    return Entidad.objects.create(clave=clave, nombre=nombre, fuente=FUENTE)


def _circuito(entidad, numero, romano, nombre):
    return CircuitoJudicial.objects.create(
        entidad=entidad,
        numero=numero,
        romano=romano,
        nombre=nombre,
        fuente=FUENTE,
    )


def _municipio(entidad, clave, nombre):
    return Municipio.objects.create(
        entidad=entidad,
        clave=clave,
        nombre=nombre,
        fuente=FUENTE,
    )


def _distrito(entidad, numero):
    return DistritoJudicialElectoral.objects.create(
        entidad=entidad,
        numero=numero,
        fuente=FUENTE,
    )


def _seccion(entidad, municipio, numero, distrito, circuito):
    seccion = SeccionElectoral.objects.create(
        entidad=entidad,
        municipio=municipio,
        numero=numero,
        fuente=FUENTE,
    )
    AsignacionDistritoJudicial.objects.create(
        seccion=seccion,
        distrito_judicial=distrito,
        circuito=circuito,
        fuente=FUENTE,
        vigencia=VIGENCIA,
    )
    return seccion
