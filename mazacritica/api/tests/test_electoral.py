from rest_framework import status
from rest_framework.test import APITestCase

from api.models import (
    Candidacy,
    Candidate,
    Election,
    ElectionZone,
    Office,
    PostalCode,
    PostalCodeZoneMapping,
)

from .helpers import create_group_user

class ElectoralApiTests(APITestCase):
    def setUp(self):
        self.editor = create_group_user(
            'editor_electoral',
            'editor-electoral@example.com',
            'password-segura',
            'editor',
        )
        self.member = create_group_user(
            'miembro_electoral',
            'miembro-electoral@example.com',
            'password-segura',
            'member',
        )

    def _as(self, user):
        self.client.force_authenticate(user=user)

    def test_visitors_read_public_records_and_only_editors_write(self):
        paths = [
            '/elections/',
            '/offices/',
            '/candidates/',
            '/candidacies/',
            '/postal-codes/',
            '/election-zones/',
        ]
        for path in paths:
            response = self.client.get(path)
            self.assertEqual(response.status_code, status.HTTP_200_OK, path)

        visitor = self.client.post(
            '/elections/',
            {'name': 'Elección ficticia', 'held_on': '2027-06-06'},
            format='json',
        )
        self._as(self.member)
        member = self.client.post(
            '/elections/',
            {'name': 'Elección ficticia', 'held_on': '2027-06-06'},
            format='json',
        )
        self._as(self.editor)
        created = self.client.post(
            '/elections/',
            {'name': 'Elección ficticia', 'held_on': '2027-06-06'},
            format='json',
        )
        self.client.force_authenticate(user=None)
        detail = self.client.get(f'/elections/{created.data["id"]}/')

        self.assertEqual(visitor.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(member.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.data['name'], 'Elección ficticia')

    def test_office_power_is_executive_legislative_or_judicial(self):
        self._as(self.editor)
        created = self.client.post(
            '/offices/',
            {'name': 'Presidencia ficticia', 'power': Office.Power.EXECUTIVE},
            format='json',
        )
        invalid = self.client.post(
            '/offices/',
            {'name': 'Cargo inválido', 'power': 'monarchy'},
            format='json',
        )
        self.client.force_authenticate(user=None)
        detail = self.client.get(f'/offices/{created.data["id"]}/')

        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.data['power'], Office.Power.EXECUTIVE)

    def test_withdrawn_and_unconfirmed_candidacies_are_not_applicable(self):
        self._as(self.editor)
        election = self.client.post(
            '/elections/',
            {'name': 'Elección local ficticia', 'held_on': '2027-06-06'},
            format='json',
        ).data
        office = self.client.post(
            '/offices/',
            {'name': 'Alcaldía ficticia', 'power': Office.Power.EXECUTIVE},
            format='json',
        ).data
        zone = self.client.post(
            '/election-zones/',
            {'name': 'Zona norte ficticia', 'code': 'ZN-01'},
            format='json',
        ).data
        confirmed = self.client.post(
            '/candidates/',
            {'name': 'Candidata Ficticia Uno'},
            format='json',
        ).data
        withdrawn = self.client.post(
            '/candidates/',
            {'name': 'Candidato Ficticio Dos'},
            format='json',
        ).data
        unconfirmed = self.client.post(
            '/candidates/',
            {'name': 'Candidata Ficticia Tres'},
            format='json',
        ).data
        self.client.post(
            '/candidacies/',
            {
                'candidate': confirmed['id'],
                'election': election['id'],
                'office': office['id'],
                'zone': zone['id'],
                'status': Candidacy.Status.CONFIRMED,
            },
            format='json',
        )
        withdrawn_response = self.client.post(
            '/candidacies/',
            {
                'candidate': withdrawn['id'],
                'election': election['id'],
                'office': office['id'],
                'zone': zone['id'],
                'status': Candidacy.Status.WITHDRAWN,
            },
            format='json',
        )
        self.client.post(
            '/candidacies/',
            {
                'candidate': unconfirmed['id'],
                'election': election['id'],
                'office': office['id'],
                'zone': zone['id'],
                'status': Candidacy.Status.UNCONFIRMED,
            },
            format='json',
        )
        self.client.force_authenticate(user=None)
        applicable = self.client.get('/candidacies/?applicable=true')
        public_detail = self.client.get(
            f'/candidacies/{withdrawn_response.data["id"]}/',
        )

        self.assertEqual(applicable.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [item['status'] for item in applicable.data],
            [Candidacy.Status.CONFIRMED],
        )
        self.assertEqual(public_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(public_detail.data['candidate'], withdrawn['id'])
        self.assertEqual(public_detail.data['election'], election['id'])
        self.assertEqual(public_detail.data['office'], office['id'])
        self.assertEqual(public_detail.data['zone'], zone['id'])

    def test_postal_search_returns_dated_zones_and_empty_payload(self):
        self._as(self.editor)
        zone_one = self.client.post(
            '/election-zones/',
            {'name': 'Zona norte ficticia', 'code': 'ZN-01'},
            format='json',
        ).data
        zone_two = self.client.post(
            '/election-zones/',
            {'name': 'Zona sur ficticia', 'code': 'ZN-02'},
            format='json',
        ).data
        postal = self.client.post(
            '/postal-codes/',
            {'code': '99020'},
            format='json',
        ).data
        unmapped = self.client.post(
            '/postal-codes/',
            {'code': '99000'},
            format='json',
        )
        self.client.post(
            '/postal-code-zone-mappings/',
            {
                'postal_code': postal['id'],
                'zone': zone_one['id'],
                'source': 'Acuerdo ficticio norte',
                'valid_from': '2024-01-01',
                'valid_to': '2027-12-31',
            },
            format='json',
        )
        self.client.post(
            '/postal-code-zone-mappings/',
            {
                'postal_code': postal['id'],
                'zone': zone_two['id'],
                'source': 'Acuerdo ficticio sur',
                'valid_from': '2025-01-01',
                'valid_to': '2028-12-31',
            },
            format='json',
        )
        invalid_dates = self.client.post(
            '/postal-code-zone-mappings/',
            {
                'postal_code': postal['id'],
                'zone': zone_one['id'],
                'source': 'Fechas invertidas',
                'valid_from': '2028-01-01',
                'valid_to': '2024-01-01',
            },
            format='json',
        )
        election = self.client.post(
            '/elections/',
            {'name': 'Elección de búsqueda', 'held_on': '2027-06-06'},
            format='json',
        ).data
        office = self.client.post(
            '/offices/',
            {'name': 'Diputación ficticia', 'power': Office.Power.LEGISLATIVE},
            format='json',
        ).data
        candidate = self.client.post(
            '/candidates/',
            {'name': 'Candidata Aplicable'},
            format='json',
        ).data
        withdrawn_candidate = self.client.post(
            '/candidates/',
            {'name': 'Candidato Retirado'},
            format='json',
        ).data
        self.client.post(
            '/candidacies/',
            {
                'candidate': candidate['id'],
                'election': election['id'],
                'office': office['id'],
                'zone': zone_one['id'],
                'status': Candidacy.Status.CONFIRMED,
            },
            format='json',
        )
        self.client.post(
            '/candidacies/',
            {
                'candidate': withdrawn_candidate['id'],
                'election': election['id'],
                'office': office['id'],
                'zone': zone_two['id'],
                'status': Candidacy.Status.WITHDRAWN,
            },
            format='json',
        )
        self.client.force_authenticate(user=None)
        found = self.client.get('/postal-code-search/?code=99020')
        empty = self.client.get('/postal-code-search/?code=99000')
        unknown = self.client.get('/postal-code-search/?code=00000')
        missing = self.client.get('/postal-code-search/')

        self.assertEqual(unmapped.status_code, status.HTTP_201_CREATED)
        self.assertEqual(invalid_dates.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(found.status_code, status.HTTP_200_OK)
        self.assertEqual(found.data['code'], '99020')
        self.assertEqual(len(found.data['zones']), 2)
        self.assertEqual(
            {zone['code'] for zone in found.data['zones']},
            {'ZN-01', 'ZN-02'},
        )
        by_code = {zone['code']: zone for zone in found.data['zones']}
        self.assertEqual(by_code['ZN-01']['valid_from'], '2024-01-01')
        self.assertEqual(by_code['ZN-01']['valid_to'], '2027-12-31')
        self.assertEqual(by_code['ZN-01']['source'], 'Acuerdo ficticio norte')
        self.assertEqual(len(by_code['ZN-01']['applicable_candidacies']), 1)
        self.assertEqual(
            by_code['ZN-01']['applicable_candidacies'][0]['status'],
            Candidacy.Status.CONFIRMED,
        )
        self.assertEqual(by_code['ZN-02']['applicable_candidacies'], [])
        self.assertEqual(empty.status_code, status.HTTP_200_OK)
        self.assertEqual(empty.data['zones'], [])
        self.assertIn('detail', empty.data)
        self.assertEqual(unknown.status_code, status.HTTP_200_OK)
        self.assertEqual(unknown.data['zones'], [])
        self.assertIn('detail', unknown.data)
        self.assertEqual(missing.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            PostalCodeZoneMapping.objects.filter(postal_code__code='99020').count(),
            2,
        )
