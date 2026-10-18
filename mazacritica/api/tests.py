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
