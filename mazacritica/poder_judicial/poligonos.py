import json
from copy import deepcopy
from datetime import date
from pathlib import Path
from urllib.request import Request, urlopen

from django.conf import settings
from django.db.models import Count

from .models import DistritoJudicialElectoral

BASE = 'https://cartografia.ine.mx/sige8/api'
FUENTE = 'INE, Sistema de Información Geográfica Electoral'
ARCHIVO = 'distritos_judiciales.geojson'
_cache = {'clave': None, 'indice': {}}


def ruta_poligonos():
    configurada = getattr(settings, 'POLIGONOS_DISTRITO_JUDICIAL', None)
    if configurada:
        return Path(configurada)
    return Path(settings.BASE_DIR) / 'PoderJudicial_Data' / ARCHIVO


def descargar_poligonos(destino, obtener=None):
    """Baja los contornos del SIGE y escribe un FeatureCollection."""
    obtener = obtener or _obtener_json
    destino = Path(destino)
    circuitos = obtener(f'{BASE}/circuito')
    features = []
    for circuito in circuitos:
        numero = int(circuito['circuito_j'])
        distritos = obtener(f'{BASE}/distritoJudicial?circuito={numero}')
        for distrito in distritos:
            clave = int(distrito['distrito_j'])
            payload = obtener(
                f'{BASE}/getDistritoJudicial?circuito={numero}&distritoJudicial={clave}'
            )
            for feature in _features(payload):
                props = feature.setdefault('properties', {})
                props['circuito_j'] = numero
                props['distrito_j'] = clave
                features.append(feature)
    documento = {
        'type': 'FeatureCollection',
        'fuente': FUENTE,
        'fecha': date.today().isoformat(),
        'features': features,
    }
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(documento), encoding='utf-8')
    return {'circuitos': len(circuitos), 'distritos': len(features)}


def poligonos_de(pares, ruta=None):
    """Devuelve el polígono solo si un distrito local tiene esa pareja.

    El circuito 8 está duplicado en el catálogo local y el 25 no existe ahí.
    En ese caso el contorno se queda en el archivo y no se asigna.
    """
    indice = cargar_indice(ruta)
    if not indice:
        return {}
    conteos = _conteos_locales()
    salida = {}
    for circuito, distrito in pares:
        clave = (int(circuito), int(distrito))
        if conteos.get(clave) == 1 and clave in indice:
            salida[clave] = indice[clave]
    return salida


def cargar_indice(ruta=None):
    path = Path(ruta) if ruta else ruta_poligonos()
    if not path.is_file():
        return {}
    stat = path.stat()
    clave = (str(path), stat.st_mtime_ns, stat.st_size)
    if _cache['clave'] == clave:
        return _cache['indice']
    documento = json.loads(path.read_text(encoding='utf-8'))
    indice = {}
    for feature in documento.get('features', []):
        props = feature.get('properties') or {}
        indice[(int(props['circuito_j']), int(props['distrito_j']))] = feature
    _cache['clave'] = clave
    _cache['indice'] = indice
    return indice


def _conteos_locales():
    rows = (
        DistritoJudicialElectoral.objects
        .values('numero', 'entidad__circuito__numero')
        .annotate(total=Count('id'))
    )
    return {
        (row['entidad__circuito__numero'], row['numero']): row['total']
        for row in rows
        if row['entidad__circuito__numero'] is not None
    }


def _obtener_json(url):
    request = Request(url, headers={'Accept': 'application/json', 'User-Agent': 'MazaCritica/0.1'})
    with urlopen(request, timeout=60) as response:
        return json.load(response)


def _features(payload):
    if isinstance(payload, list):
        payload = payload[0] if payload else {}
    features = payload.get('features') or []
    return [deepcopy(feature) for feature in features]
