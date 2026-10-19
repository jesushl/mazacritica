from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import (
    Candidacy,
    Candidate,
    Election,
    ElectionZone,
    Office,
    PostalCode,
    PostalCodeZoneMapping,
)
from api.permissions import IsEditor
from api.serializers.electoral import (
    CandidacySerializer,
    CandidateSerializer,
    ElectionSerializer,
    ElectionZoneSerializer,
    OfficeSerializer,
    PostalCodeSerializer,
    PostalCodeZoneMappingSerializer,
)

class EditorWriteMixin:
    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsEditor()]
        return [permissions.AllowAny()]


class ElectionViewSet(EditorWriteMixin, viewsets.ModelViewSet):
    queryset = Election.objects.all()
    serializer_class = ElectionSerializer


class OfficeViewSet(EditorWriteMixin, viewsets.ModelViewSet):
    queryset = Office.objects.all()
    serializer_class = OfficeSerializer


class CandidateViewSet(EditorWriteMixin, viewsets.ModelViewSet):
    queryset = Candidate.objects.all()
    serializer_class = CandidateSerializer


class ElectionZoneViewSet(EditorWriteMixin, viewsets.ModelViewSet):
    queryset = ElectionZone.objects.all()
    serializer_class = ElectionZoneSerializer


class PostalCodeViewSet(EditorWriteMixin, viewsets.ModelViewSet):
    queryset = PostalCode.objects.all()
    serializer_class = PostalCodeSerializer


class CandidacyViewSet(EditorWriteMixin, viewsets.ModelViewSet):
    serializer_class = CandidacySerializer

    def get_queryset(self):
        queryset = Candidacy.objects.all()
        if self.request.query_params.get('applicable') == 'true':
            queryset = queryset.filter(status=Candidacy.Status.CONFIRMED)
        return queryset


class PostalCodeZoneMappingViewSet(EditorWriteMixin, viewsets.ModelViewSet):
    queryset = PostalCodeZoneMapping.objects.all()
    serializer_class = PostalCodeZoneMappingSerializer


class PostalCodeSearchView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, format=None):
        code = str(request.query_params.get('code') or '').strip()
        if not code:
            return Response(
                {'detail': 'Indica un código postal.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        mappings = PostalCodeZoneMapping.objects.filter(
            postal_code__code=code,
        ).select_related('zone')
        if not mappings.exists():
            return Response({
                'code': code,
                'zones': [],
                'detail': (
                    'No hay zonas oficiales registradas para este código postal.'
                ),
            })
        zones = []
        for mapping in mappings:
            applicable = Candidacy.objects.filter(
                zone=mapping.zone,
                status=Candidacy.Status.CONFIRMED,
            )
            zones.append({
                'id': mapping.zone_id,
                'name': mapping.zone.name,
                'code': mapping.zone.code,
                'valid_from': mapping.valid_from.isoformat(),
                'valid_to': mapping.valid_to.isoformat(),
                'source': mapping.source,
                'applicable_candidacies': CandidacySerializer(
                    applicable,
                    many=True,
                ).data,
            })
        return Response({'code': code, 'zones': zones})
