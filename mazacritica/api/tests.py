from django.contrib.auth.models import Group, User
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Note, Source, Tag, UserProfile


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
        self.user.groups.add(Group.objects.get_or_create(name='editor')[0])
        self.member = User.objects.create_user(
            username='miembro',
            email='miembro@example.com',
            password='password-segura',
        )
        self.member.groups.add(Group.objects.get_or_create(name='member')[0])
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
        self.draft = Note.objects.create(
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

    def test_member_reads_published_notes_only(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.get('/notes/')
        draft_response = self.client.get(f'/notes/{self.draft.id}/')
        filtered = self.client.get('/notes/?status=draft')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [item['id'] for item in response.data],
            [self.published_note.id],
        )
        self.assertEqual(draft_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(filtered.data, [])

    def test_drafts_are_hidden_from_anonymous_users_and_members(self):
        anonymous_list = self.client.get('/notes/')
        anonymous_draft = self.client.get(f'/notes/{self.draft.id}/')
        self.client.force_authenticate(user=self.member)
        member_list = self.client.get('/notes/')
        member_draft = self.client.get(f'/notes/{self.draft.id}/')

        self.assertEqual(
            [item['id'] for item in anonymous_list.data],
            [self.published_note.id],
        )
        self.assertEqual(anonymous_draft.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            [item['id'] for item in member_list.data],
            [self.published_note.id],
        )
        self.assertEqual(member_draft.status_code, status.HTTP_404_NOT_FOUND)

    def test_member_cannot_create_update_or_delete_notes_tags_or_sources(self):
        self.client.force_authenticate(user=self.member)
        responses = [
            self.client.post(
                '/notes/',
                {
                    'title': 'Nota de un miembro',
                    'content': 'No debe crearse.',
                    'source': self.source.id,
                },
                format='json',
            ),
            self.client.patch(
                f'/notes/{self.published_note.id}/',
                {'title': 'Cambio no permitido'},
                format='json',
            ),
            self.client.delete(f'/notes/{self.published_note.id}/'),
            self.client.post(
                '/tags/',
                {'name': 'Etiqueta de miembro'},
                format='json',
            ),
            self.client.patch(
                f'/tags/{self.tag.id}/',
                {'description': 'Cambio no permitido'},
                format='json',
            ),
            self.client.delete(f'/tags/{self.tag.id}/'),
            self.client.post(
                '/sources/',
                {
                    'name': 'Fuente de miembro',
                    'url': 'https://example.com/miembro',
                },
                format='json',
            ),
            self.client.patch(
                f'/sources/{self.source.id}/',
                {'publisher': 'Cambio no permitido'},
                format='json',
            ),
            self.client.delete(f'/sources/{self.source.id}/'),
        ]

        self.assertTrue(all(
            response.status_code == status.HTTP_403_FORBIDDEN
            for response in responses
        ))
        self.assertFalse(Note.objects.filter(title='Nota de un miembro').exists())

    def test_editor_can_publish_edit_and_archive_notes(self):
        self.client.force_authenticate(user=self.user)
        created = self.client.post(
            '/notes/',
            {
                'title': 'Nota del editor',
                'content': 'Contenido editorial.',
                'source': self.source.id,
                'status': Note.EditorialStatus.PUBLISHED,
                'published_at': self.published_at.isoformat(),
                'author': self.member.id,
            },
            format='json',
        )
        edited = self.client.patch(
            f'/notes/{created.data["id"]}/',
            {'excerpt': 'Resumen editado.'},
            format='json',
        )
        archived = self.client.patch(
            f'/notes/{created.data["id"]}/',
            {'status': Note.EditorialStatus.ARCHIVED},
            format='json',
        )
        note = Note.objects.get(pk=created.data['id'])
        visible = self.client.get('/notes/')

        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(edited.status_code, status.HTTP_200_OK)
        self.assertEqual(archived.status_code, status.HTTP_200_OK)
        self.assertEqual(note.author, self.user)
        self.assertEqual(note.status, Note.EditorialStatus.ARCHIVED)
        self.assertEqual(note.excerpt, 'Resumen editado.')
        self.assertIn(self.draft.id, [item['id'] for item in visible.data])

    def test_editor_can_manage_tags_and_sources(self):
        self.client.force_authenticate(user=self.user)
        tag = self.client.post(
            '/tags/',
            {'name': 'Tema editorial de prueba', 'kind': 'topic'},
            format='json',
        )
        tag_update = self.client.patch(
            f'/tags/{tag.data["id"]}/',
            {'description': 'Estado neutral.'},
            format='json',
        )
        source = self.client.post(
            '/sources/',
            {
                'name': 'Fuente editorial',
                'url': 'https://example.com/editorial',
            },
            format='json',
        )
        source_update = self.client.patch(
            f'/sources/{source.data["id"]}/',
            {'publisher': 'Redacción'},
            format='json',
        )
        source_delete = self.client.delete(f'/sources/{source.data["id"]}/')
        tag_delete = self.client.delete(f'/tags/{tag.data["id"]}/')

        self.assertEqual(tag.status_code, status.HTTP_201_CREATED)
        self.assertEqual(tag_update.status_code, status.HTTP_200_OK)
        self.assertEqual(source.status_code, status.HTTP_201_CREATED)
        self.assertEqual(source_update.status_code, status.HTTP_200_OK)
        self.assertEqual(source_delete.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(tag_delete.status_code, status.HTTP_204_NO_CONTENT)


class AuthApiTests(APITestCase):
    def test_register_creates_user_profile_and_member_group(self):
        response = self.client.post(
            '/register/',
            {
                'email': 'ana@example.com',
                'password': 'password-segura',
                'nickname': 'Ana_01',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email='ana@example.com')
        self.assertEqual(user.username, 'ana_01')
        self.assertTrue(user.check_password('password-segura'))
        self.assertNotEqual(user.password, 'password-segura')
        self.assertEqual(user.profile.nickname, 'ana_01')
        self.assertEqual(response.data['nickname'], 'ana_01')
        self.assertEqual(response.data['email'], 'ana@example.com')
        self.assertTrue(user.groups.filter(name='member').exists())

    def test_register_rejects_duplicate_email(self):
        self.client.post(
            '/register/',
            {
                'email': 'ana@example.com',
                'password': 'password-segura',
                'nickname': 'ana_01',
            },
            format='json',
        )
        response = self.client.post(
            '/register/',
            {
                'email': 'Ana@Example.com',
                'password': 'otra-password-segura',
                'nickname': 'ana_02',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)

    def test_register_rejects_duplicate_nickname(self):
        self.client.post(
            '/register/',
            {
                'email': 'ana@example.com',
                'password': 'password-segura',
                'nickname': 'ana_01',
            },
            format='json',
        )
        response = self.client.post(
            '/register/',
            {
                'email': 'otra@example.com',
                'password': 'password-segura',
                'nickname': 'ANA_01',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(UserProfile.objects.count(), 1)

    def test_register_rejects_invalid_nickname(self):
        for nickname in ('ab', 'bad-name', 'has space', 'a' * 31, ''):
            response = self.client.post(
                '/register/',
                {
                    'email': 'ana@example.com',
                    'password': 'password-segura',
                    'nickname': nickname,
                },
                format='json',
            )
            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
                nickname,
            )

        self.assertEqual(User.objects.count(), 0)

    def test_login_with_email_or_username_returns_token(self):
        self.client.post(
            '/register/',
            {
                'email': 'ana@example.com',
                'password': 'password-segura',
                'nickname': 'ana_01',
            },
            format='json',
        )
        user = User.objects.get(username='ana_01')
        user.groups.add(Group.objects.get_or_create(name='editor')[0])

        by_email = self.client.post(
            '/login/',
            {'email': 'ana@example.com', 'password': 'password-segura'},
            format='json',
        )
        by_username = self.client.post(
            '/login/',
            {'username': 'ana_01', 'password': 'password-segura'},
            format='json',
        )

        for response in (by_email, by_username):
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['nickname'], 'ana_01')
            self.assertEqual(response.data['email'], 'ana@example.com')
            self.assertCountEqual(response.data['groups'], ['member', 'editor'])
            self.assertTrue(Token.objects.filter(key=response.data['token'], user=user).exists())

    def test_login_rejects_bad_credentials(self):
        self.client.post(
            '/register/',
            {
                'email': 'ana@example.com',
                'password': 'password-segura',
                'nickname': 'ana_01',
            },
            format='json',
        )
        response = self.client.post(
            '/login/',
            {'email': 'ana@example.com', 'password': 'incorrecta'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_deletes_token(self):
        self.client.post(
            '/register/',
            {
                'email': 'ana@example.com',
                'password': 'password-segura',
                'nickname': 'ana_01',
            },
            format='json',
        )
        login = self.client.post(
            '/login/',
            {'username': 'ana_01', 'password': 'password-segura'},
            format='json',
        )
        token = login.data['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        response = self.client.post('/logout/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Token.objects.filter(key=token).exists())

    def test_logout_and_me_require_token(self):
        logout = self.client.post('/logout/')
        me = self.client.get('/me/')

        self.assertEqual(logout.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(me.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_profile(self):
        self.client.post(
            '/register/',
            {
                'email': 'ana@example.com',
                'password': 'password-segura',
                'nickname': 'ana_01',
            },
            format='json',
        )
        login = self.client.post(
            '/login/',
            {'email': 'ana@example.com', 'password': 'password-segura'},
            format='json',
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {login.data["token"]}')
        response = self.client.get('/me/')

        user = User.objects.get(username='ana_01')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], user.id)
        self.assertEqual(response.data['email'], 'ana@example.com')
        self.assertEqual(response.data['nickname'], 'ana_01')
        self.assertCountEqual(response.data['groups'], ['member'])
