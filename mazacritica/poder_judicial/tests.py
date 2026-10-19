from datetime import date

from django.core.management import call_command
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import (
    Candidacy,
    Candidate,
    Election,
    ElectionZone,
    Note,
    Office,
    PostalCode,
    PostalCodeZoneMapping,
    Source,
    Tag,
)

from .models import NoteMention


class JudicialDistrictTests(APITestCase):
    def setUp(self):
        source = Source.objects.create(
            name='Fuente judicial ficticia',
            url='https://example.test/judicial',
        )
        tag = Tag.objects.create(name='Señalamiento de distrito', kind='status')
        self.published = Note.objects.create(
            title='Nota judicial publicada',
            content='Contenido publicado.',
            excerpt='Resumen publicado.',
            status=Note.EditorialStatus.PUBLISHED,
            source=source,
            published_at=timezone.now(),
        )
        self.published.tags.add(tag)
        self.draft = Note.objects.create(
            title='Nota judicial borrador',
            content='Borrador.',
            status=Note.EditorialStatus.DRAFT,
            source=source,
        )
        election = Election.objects.create(name='Elección judicial', held_on=date(2027, 6, 1))
        judicial = Office.objects.create(name='Magistratura de prueba', power=Office.Power.JUDICIAL)
        executive = Office.objects.create(name='Presidencia de prueba', power=Office.Power.EXECUTIVE)
        north = ElectionZone.objects.create(name='Distrito norte', code='DJ-N')
        south = ElectionZone.objects.create(name='Distrito sur', code='DJ-S')
        self.mentioned = Candidate.objects.create(name='Aspirante Mencionada')
        quiet = Candidate.objects.create(name='Aspirante Sin Nota')
        executive_person = Candidate.objects.create(name='Aspirante Ejecutivo')
        withdrawn = Candidate.objects.create(name='Aspirante Retirada')
        Candidacy.objects.create(
            candidate=self.mentioned, election=election, office=judicial, zone=north,
        )
        Candidacy.objects.create(
            candidate=quiet, election=election, office=judicial, zone=south,
        )
        Candidacy.objects.create(
            candidate=executive_person, election=election, office=executive, zone=north,
        )
        Candidacy.objects.create(
            candidate=withdrawn, election=election, office=judicial, zone=north,
            status=Candidacy.Status.WITHDRAWN,
        )
        postal = PostalCode.objects.create(code='88010')
        PostalCode.objects.create(code='88000')
        PostalCodeZoneMapping.objects.create(
            postal_code=postal, zone=north, source='Acuerdo norte',
            valid_from=date(2024, 1, 1), valid_to=date(2027, 12, 31),
        )
        PostalCodeZoneMapping.objects.create(
            postal_code=postal, zone=south, source='Acuerdo sur',
            valid_from=date(2025, 1, 1), valid_to=date(2028, 12, 31),
        )
        NoteMention.objects.create(candidate=self.mentioned, note=self.published)
        NoteMention.objects.create(candidate=self.mentioned, note=self.draft)

    def test_district_lists_judicial_aspirants_and_published_notes_only(self):
        response = self.client.get('/poder-judicial/distrito/?code=88010')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {zone['code'] for zone in response.data['zones']},
            {'DJ-N', 'DJ-S'},
        )
        by_name = {item['name']: item for item in response.data['aspirantes']}
        self.assertEqual(set(by_name), {'Aspirante Mencionada', 'Aspirante Sin Nota'})
        notes = by_name['Aspirante Mencionada']['notes']
        self.assertEqual([note['title'] for note in notes], ['Nota judicial publicada'])
        self.assertIn('Señalamiento de distrito', notes[0]['tags'])
        self.assertEqual(by_name['Aspirante Sin Nota']['notes'], [])
        self.assertEqual(by_name['Aspirante Mencionada']['office'], 'Magistratura de prueba')

    def test_unmapped_postal_code_returns_an_empty_district(self):
        response = self.client.get('/poder-judicial/distrito/?code=88000')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['zones'], [])
        self.assertEqual(response.data['aspirantes'], [])
        self.assertIn('detail', response.data)

    def test_missing_code_is_rejected(self):
        response = self.client.get('/poder-judicial/distrito/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SeededJudicialDistrictTests(APITestCase):
    def test_demo_postal_code_shows_judicial_aspirants_and_published_notes(self):
        call_command('seed_demo_data')
        response = self.client.get('/poder-judicial/distrito/?code=99020')
        by_name = {item['name']: item for item in response.data['aspirantes']}
        self.assertEqual(
            set(by_name),
            {'Aspirante Judicial Ficticia', 'Aspirante Judicial Sin Nota'},
        )
        notes = by_name['Aspirante Judicial Ficticia']['notes']
        self.assertEqual([note['title'] for note in notes], ['Nota publicada ficticia'])
        self.assertIn('Señalamiento', notes[0]['tags'])
        self.assertEqual(by_name['Aspirante Judicial Sin Nota']['notes'], [])
