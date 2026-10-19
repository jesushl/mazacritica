from django.db.models import Count

from .models import AsignacionDistritoJudicial, CodigoPostal, EmpalmePostalJudicial


def regiones_de_municipio(entidad_clave, municipio_clave):
    """Distritos judiciales del corte oficial para un municipio.

    Devuelve todas las regiones que tocan ese municipio. No elige una.
    """
    rows = (
        AsignacionDistritoJudicial.objects.filter(
            seccion__entidad__clave=entidad_clave,
            seccion__municipio__clave=municipio_clave,
        )
        .values(
            'distrito_judicial__numero',
            'circuito__numero',
            'circuito__romano',
            'circuito__nombre',
        )
        .annotate(secciones=Count('id'))
        .order_by('distrito_judicial__numero', 'circuito__numero')
    )
    return [
        {
            'numero': row['distrito_judicial__numero'],
            'circuito': {
                'numero': row['circuito__numero'],
                'romano': row['circuito__romano'],
                'nombre': row['circuito__nombre'],
            },
            'secciones': row['secciones'],
        }
        for row in rows
    ]


def buscar_codigo_postal(codigo):
    """Cruce de un código postal SEPOMEX con los distritos judiciales del municipio.

    Si el municipio no tiene cruce seguro, la lista de distritos va vacía.
    No elige un distrito cuando hay varios.
    """
    texto = str(codigo).strip()
    if texto.isdigit():
        texto = texto.zfill(5)
    postal = (
        CodigoPostal.objects.select_related(
            'municipio',
            'municipio__municipio',
            'municipio__municipio__entidad',
        )
        .filter(codigo=texto)
        .first()
    )
    if postal is None:
        return None

    sepomex = postal.municipio
    judicial = sepomex.municipio
    empalme = EmpalmePostalJudicial.objects.order_by('id').first()
    return {
        'codigo': postal.codigo,
        'municipio_sepomex': {
            'c_estado': sepomex.c_estado,
            'c_mnpio': sepomex.c_mnpio,
            'nombre': sepomex.nombre,
            'nombre_estado': sepomex.nombre_estado,
        },
        'municipio': None if judicial is None else {
            'clave': judicial.clave,
            'nombre': judicial.nombre,
            'entidad': judicial.entidad.clave,
        },
        'criterio': empalme.criterio if empalme else 'nombre_en_entidad',
        'vigencia': (
            empalme.vigencia.isoformat() if empalme else '2025-02-10'
        ),
        'distritos': (
            []
            if judicial is None
            else regiones_de_municipio(judicial.entidad.clave, judicial.clave)
        ),
        'asentamientos': [
            {'nombre': item.nombre, 'tipo': item.tipo}
            for item in postal.asentamientos.order_by('nombre', 'clave')
        ],
    }
