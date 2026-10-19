from collections import defaultdict

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import Candidacy, Note, Office, PostalCodeZoneMapping

from .models import NoteMention
from .regiones import buscar_codigo_postal


class DistrictView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, format=None):
        code = str(request.query_params.get('code') or '').strip()
        if not code:
            return Response(
                {'detail': 'Indica un código postal.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        official = buscar_codigo_postal(code)
        if official is not None:
            return Response(_official_district_payload(official))

        mappings = PostalCodeZoneMapping.objects.filter(
            postal_code__code=code,
        ).select_related('zone')
        zones = [
            {
                'id': mapping.zone_id,
                'name': mapping.zone.name,
                'code': mapping.zone.code,
                'valid_from': mapping.valid_from.isoformat(),
                'valid_to': mapping.valid_to.isoformat(),
                'source': mapping.source,
            }
            for mapping in mappings
        ]
        if not zones:
            return Response({
                'code': code,
                'zones': [],
                'aspirantes': [],
                'detail': (
                    'No hay zonas oficiales registradas para este código postal.'
                ),
            })
        candidacies = Candidacy.objects.filter(
            zone_id__in=[zone['id'] for zone in zones],
            office__power=Office.Power.JUDICIAL,
            status=Candidacy.Status.CONFIRMED,
        ).select_related('candidate', 'office', 'election', 'zone')
        mentions = NoteMention.objects.filter(
            candidate_id__in=[item.candidate_id for item in candidacies],
            note__status=Note.EditorialStatus.PUBLISHED,
        ).select_related('note').prefetch_related('note__tags')
        notes_by_candidate = defaultdict(list)
        for mention in mentions:
            notes_by_candidate[mention.candidate_id].append({
                'id': mention.note_id,
                'title': mention.note.title,
                'excerpt': mention.note.excerpt,
                'tags': [tag.name for tag in mention.note.tags.all()],
            })
        aspirantes = [
            {
                'id': candidacy.candidate_id,
                'name': candidacy.candidate.name,
                'office': candidacy.office.name,
                'election': candidacy.election.name,
                'zone': {
                    'code': candidacy.zone.code,
                    'name': candidacy.zone.name,
                },
                'status': candidacy.status,
                'notes': notes_by_candidate.get(candidacy.candidate_id, []),
            }
            for candidacy in candidacies
        ]
        return Response({
            'code': code,
            'zones': zones,
            'aspirantes': aspirantes,
            'detail': '',
        })


def _official_district_payload(found):
    municipio = found['municipio_sepomex']
    zones = []
    for district in found['distritos']:
        entidad = found['municipio']['entidad']
        zones.append({
            'id': f'{entidad}-{district["numero"]}',
            'name': f'Distrito judicial {district["numero"]}',
            'code': f'DJ-{entidad}-{district["numero"]}',
            'valid_from': found['vigencia'],
            'valid_to': found['vigencia'],
            'source': district['circuito']['nombre'],
            'secciones': district['secciones'],
        })
    if zones:
        detail = ''
    elif found['municipio'] is None:
        detail = (
            f"{municipio['nombre']} está en el catálogo postal, "
            'pero no tiene un distrito judicial en el corte del 10 de febrero de 2025.'
        )
    else:
        detail = 'No hay distritos judiciales para este código postal.'
    return {
        'code': found['codigo'],
        'zones': zones,
        'aspirantes': [],
        'municipio': municipio['nombre'],
        'estado': municipio['nombre_estado'],
        'asentamientos': found['asentamientos'],
        'detail': detail,
    }
