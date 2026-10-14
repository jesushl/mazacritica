from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Note, Source, Tag


class ContentModelTests(APITestCase):
    def setUp(self):
        self.source = Source.objects.create(
            name='Fuente de prueba',
            url='https://example.com/nota',
        )
        self.tag = Tag.objects.create(name='Etiqueta de prueba', kind='topic')

    def test_note_has_relational_tags_and_source(self):
        note = Note.objects.create(
            title='Nota de prueba',
            content='Contenido documentado.',
            source=self.source,
        )
        note.tags.add(self.tag)

        self.assertEqual(note.source, self.source)
        self.assertIn(note, self.tag.notes.all())
        self.assertEqual(note.slug, 'nota-de-prueba')


class ContentApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='editor@example.com',
            email='editor@example.com',
            password='password-segura',
        )
        self.source = Source.objects.create(
            name='Fuente de prueba',
            url='https://example.com/fuente',
        )
        self.tag = Tag.objects.create(name='Señalamiento de prueba', kind='status')
        self.published_at = timezone.now()
        self.published_note = Note.objects.create(
            title='Nota publicada',
            content='Contenido publicado.',
            source=self.source,
            status=Note.EditorialStatus.PUBLISHED,
            published_at=self.published_at,
        )
        self.published_note.tags.add(self.tag)
        Note.objects.create(
            title='Borrador privado',
            content='Contenido en revisión.',
            source=self.source,
        )

    def test_anonymous_users_only_see_published_notes(self):
        response = self.client.get('/notes/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.published_note.id)

    def test_authenticated_user_can_create_note_with_tags(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/notes/',
            {
                'title': 'Nueva nota',
                'content': 'Contenido de la nueva nota.',
                'source': self.source.id,
                'tags': [self.tag.id],
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        note = Note.objects.get(title='Nueva nota')
        self.assertEqual(note.author, self.user)
        self.assertEqual(list(note.tags.values_list('id', flat=True)), [self.tag.id])

    def test_note_can_be_filtered_by_tag_and_date(self):
        date = self.published_at.date().isoformat()
        response = self.client.get(
            f'/notes/?tag={self.tag.slug}&date_from={date}&date_to={date}',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_published_note_requires_publication_date(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/notes/',
            {
                'title': 'Publicación sin fecha',
                'content': 'Contenido.',
                'source': self.source.id,
                'status': Note.EditorialStatus.PUBLISHED,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('published_at', response.data)
