from unittest.mock import patch

from django.contrib.auth.models import Group, User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from api.models import UserProfile

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
        self.assertFalse(User.objects.filter(username='ana_02').exists())

    def test_register_rejects_duplicate_email_when_precheck_is_bypassed(self):
        User.objects.create_user(
            username='existente',
            email='ana@example.com',
            password='password-segura',
        )
        real_filter = User.objects.filter

        def filter_without_email_precheck(*args, **kwargs):
            if set(kwargs) == {'email__iexact'}:
                return User.objects.none()
            return real_filter(*args, **kwargs)

        with patch(
            'api.serializers.auth.User.objects.filter',
            side_effect=filter_without_email_precheck,
        ):
            response = self.client.post(
                '/register/',
                {
                    'email': 'ANA@example.com',
                    'password': 'password-segura',
                    'nickname': 'ana_02',
                },
                format='json',
            )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username='ana_02').exists())
        self.assertEqual(
            User.objects.filter(email__iexact='ana@example.com').count(),
            1,
        )

    def test_login_and_me_create_missing_profile(self):
        user = User.objects.create_user(
            username='Sin_Perfil',
            email='sin@example.com',
            password='password-segura',
        )
        admin = User.objects.create_superuser(
            username='root_admin',
            email='root@example.com',
            password='password-segura',
        )
        self.assertFalse(UserProfile.objects.filter(user=user).exists())
        self.assertFalse(UserProfile.objects.filter(user=admin).exists())

        login = self.client.post(
            '/login/',
            {'username': 'Sin_Perfil', 'password': 'password-segura'},
            format='json',
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.assertEqual(login.data['nickname'], 'sin_perfil')
        self.assertTrue(
            UserProfile.objects.filter(user=user, nickname='sin_perfil').exists()
        )

        admin_login = self.client.post(
            '/login/',
            {'email': 'root@example.com', 'password': 'password-segura'},
            format='json',
        )
        self.assertEqual(admin_login.status_code, status.HTTP_200_OK)
        self.assertEqual(admin_login.data['nickname'], 'root_admin')
        self.assertIn('token', admin_login.data)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {admin_login.data["token"]}',
        )
        me = self.client.get('/me/')
        self.assertEqual(me.status_code, status.HTTP_200_OK)
        self.assertEqual(me.data['id'], admin.id)
        self.assertEqual(me.data['nickname'], 'root_admin')

        bare = User.objects.create_user(
            username='ya_token',
            email='token@example.com',
            password='password-segura',
        )
        token = Token.objects.create(user=bare)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        bare_me = self.client.get('/me/')
        self.assertEqual(bare_me.status_code, status.HTTP_200_OK)
        self.assertEqual(bare_me.data['nickname'], 'ya_token')
        self.assertTrue(UserProfile.objects.filter(user=bare).exists())

    def test_login_without_usable_nickname_does_not_issue_token(self):
        user = User.objects.create_user(
            username='no',
            email='corto@example.com',
            password='password-segura',
        )
        response = self.client.post(
            '/login/',
            {'username': 'no', 'password': 'password-segura'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', response.data)
        self.assertFalse(Token.objects.filter(user=user).exists())

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
        self.assertEqual(response.data['detail'], 'Credenciales inválidas.')

    def test_login_rejects_inactive_user_with_valid_password(self):
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
        user.is_active = False
        user.save(update_fields=['is_active'])

        response = self.client.post(
            '/login/',
            {'email': 'ana@example.com', 'password': 'password-segura'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], 'Credenciales inválidas.')
        self.assertNotIn('token', response.data)
        self.assertFalse(Token.objects.filter(user=user).exists())

    def test_register_rejects_short_or_common_password(self):
        for password in ('short', 'password'):
            response = self.client.post(
                '/register/',
                {
                    'email': 'ana@example.com',
                    'password': password,
                    'nickname': 'ana_01',
                },
                format='json',
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('password', response.data)

        self.assertEqual(User.objects.count(), 0)

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
