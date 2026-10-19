import json
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from .models import (
    AsignacionDistritoJudicial,
    CircuitoJudicial,
    CodigoPostal,
    DistritoJudicialElectoral,
    Entidad,
    Municipio,
    SeccionElectoral,
    SepomexMunicipio,
)
FUENTE = 'prueba'
VIGENCIA = date(2025, 2, 10)


class PoligonosDistritoTests(TestCase):
    def test_descarga_y_no_asigna_el_circuito_duplicado(self):
        with TemporaryDirectory() as temporary:
            destino = Path(temporary) / 'distritos_judiciales.geojson'
            with patch('poder_judicial.poligonos._obtener_json', side_effect=_obtener_falso):
                call_command('load_poligonos_distrito', destino=str(destino))
            documento = json.loads(destino.read_text(encoding='utf-8'))
            self.assertEqual(documento['fuente'], 'INE, Sistema de Información Geográfica Electoral')
            self.assertEqual(documento['fecha'], date.today().isoformat())
            self.assertEqual(
                sorted(
                    (item['properties']['circuito_j'], item['properties']['distrito_j'])
                    for item in documento['features']
                ),
                [(1, 6), (8, 1), (25, 1)],
            )

            _catalogo()
            with override_settings(POLIGONOS_DISTRITO_JUDICIAL=str(destino)):
                response = APIClient().get('/poder-judicial/distrito/?code=07279')
                coahuila = APIClient().get('/poder-judicial/distrito/?code=27000')

        self.assertEqual(response.status_code, 200)
        zone = response.data['zones'][0]
        self.assertEqual(zone['code'], 'DJ-9-6')
        self.assertEqual(zone['poligono']['properties']['circuito_j'], 1)
        self.assertEqual(zone['poligono']['properties']['distrito_j'], 6)
        self.assertEqual(zone['poligono']['geometry']['coordinates'][0][0][0][0], [-99.1, 19.4])

        self.assertEqual([item['code'] for item in coahuila.data['zones']], ['DJ-5-1'])
        self.assertNotIn('poligono', coahuila.data['zones'][0])
        self.assertNotIn('-104.2', json.dumps(coahuila.data))


def _obtener_falso(url):
    if url.endswith('/circuito'):
        return [{'circuito_j': 1}, {'circuito_j': 8}, {'circuito_j': 25}]
    if url.endswith('circuito=1'):
        return [{'distrito_j': 6}]
    if url.endswith('circuito=8'):
        return [{'distrito_j': 1}]
    if url.endswith('circuito=25'):
        return [{'distrito_j': 1}]
    if 'circuito=1&distritoJudicial=6' in url:
        return [_feature(1, 6, [-99.1, 19.4])]
    if 'circuito=8&distritoJudicial=1' in url:
        return [_feature(8, 1, [-103.4, 25.5])]
    if 'circuito=25&distritoJudicial=1' in url:
        return [_feature(25, 1, [-104.2, 24.0])]
    raise AssertionError(url)


def _feature(circuito, distrito, punto):
    return {
        'type': 'FeatureCollection',
        'features': [{
            'type': 'Feature',
            'properties': {'circuito_j': circuito, 'distrito_j': distrito},
            'geometry': {'type': 'MultiPolygon', 'coordinates': [[[[punto, punto, punto, punto]]]]},
        }],
    }


def _catalogo():
    cdmx = Entidad.objects.create(clave=9, nombre='CIUDAD DE MEXICO', fuente=FUENTE)
    coahuila = Entidad.objects.create(clave=5, nombre='COAHUILA', fuente=FUENTE)
    durango = Entidad.objects.create(clave=10, nombre='COAHUILA', fuente=FUENTE)
    circuito_cdmx = CircuitoJudicial.objects.create(
        entidad=cdmx, numero=1, romano='I', nombre='CIUDAD DE MEXICO', fuente=FUENTE,
    )
    circuito_coahuila = CircuitoJudicial.objects.create(
        entidad=coahuila, numero=8, romano='VIII', nombre='COAHUILA', fuente=FUENTE,
    )
    CircuitoJudicial.objects.create(
        entidad=durango, numero=8, romano='VIII', nombre='COAHUILA', fuente=FUENTE,
    )
    gam = Municipio.objects.create(entidad=cdmx, clave=5, nombre='GUSTAVO A MADERO', fuente=FUENTE)
    torreon = Municipio.objects.create(entidad=coahuila, clave=35, nombre='TORREON', fuente=FUENTE)
    distrito_gam = DistritoJudicialElectoral.objects.create(entidad=cdmx, numero=6, fuente=FUENTE)
    distrito_torreon = DistritoJudicialElectoral.objects.create(entidad=coahuila, numero=1, fuente=FUENTE)
    DistritoJudicialElectoral.objects.create(entidad=durango, numero=1, fuente=FUENTE)
    _seccion(cdmx, gam, 1, distrito_gam, circuito_cdmx)
    _seccion(coahuila, torreon, 1, distrito_torreon, circuito_coahuila)
    _postal(9, 5, '07279', 'GUSTAVO A MADERO', 'Ciudad de México', gam)
    _postal(5, 35, '27000', 'TORREON', 'Coahuila', torreon)


def _seccion(entidad, municipio, numero, distrito, circuito):
    seccion = SeccionElectoral.objects.create(
        entidad=entidad, municipio=municipio, numero=numero, fuente=FUENTE,
    )
    AsignacionDistritoJudicial.objects.create(
        seccion=seccion,
        distrito_judicial=distrito,
        circuito=circuito,
        fuente=FUENTE,
        vigencia=VIGENCIA,
    )


def _postal(c_estado, c_mnpio, codigo, nombre, estado, municipio):
    sepomex = SepomexMunicipio.objects.create(
        c_estado=c_estado,
        c_mnpio=c_mnpio,
        nombre=nombre,
        nombre_estado=estado,
        municipio=municipio,
    )
    CodigoPostal.objects.create(codigo=codigo, municipio=sepomex)
