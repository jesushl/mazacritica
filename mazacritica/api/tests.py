from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import (
    Comment,
    CommentReport,
    ModerationAction,
    Note,
    Source,
    Tag,
    UserProfile,
)


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
            'api.serializers.User.objects.filter',
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


class CommentApiTests(APITestCase):
    def setUp(self):
        self.editor = self._user('editor_demo', 'editor@example.com', 'editor')
        self.member = self._user('miembro_uno', 'miembro@example.com', 'member')
        self.other = self._user('miembro_dos', 'otro@example.com', 'member')
        self.moderator = self._user('modera_demo', 'modera@example.com', 'moderator')
        self.source = Source.objects.create(
            name='Fuente de comentarios',
            url='https://example.com/comentarios',
        )
        self.note = Note.objects.create(
            title='Nota comentable',
            content='Contenido publicado.',
            source=self.source,
            status=Note.EditorialStatus.PUBLISHED,
            published_at=timezone.now(),
        )
        self.other_note = Note.objects.create(
            title='Otra nota',
            content='Otro contenido.',
            source=self.source,
            status=Note.EditorialStatus.PUBLISHED,
            published_at=timezone.now(),
        )

    def _user(self, nickname, email, group_name):
        user = User.objects.create_user(
            username=nickname,
            email=email,
            password='password-segura',
        )
        UserProfile.objects.create(user=user, nickname=nickname)
        user.groups.add(Group.objects.get_or_create(name=group_name)[0])
        return user

    def _token(self, user):
        token, _created = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    def _comment(self, note, author, body, status, parent=None):
        return Comment.objects.create(
            note=note,
            author=author,
            parent=parent,
            nickname=author.profile.nickname,
            body=body,
            status=status,
        )

    def test_member_comment_stores_profile_nickname_and_starts_pending(self):
        self._token(self.member)
        response = self.client.post(
            f'/notes/{self.note.id}/comments/',
            {'body': 'Un comentario.', 'nickname': 'otro_nombre'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], Comment.Status.PENDING)
        self.assertIsNone(response.data['parent'])
        self.assertEqual(response.data['nickname'], 'miembro_uno')
        comment = Comment.objects.get(pk=response.data['id'])
        self.assertEqual(comment.author, self.member)
        self.assertEqual(comment.note, self.note)
        self.assertEqual(comment.nickname, 'miembro_uno')

    def test_public_get_returns_only_visible_comments_and_direct_replies(self):
        visible = self._comment(
            self.note, self.member, 'Visible', Comment.Status.VISIBLE,
        )
        self._comment(self.note, self.member, 'Pendiente', Comment.Status.PENDING)
        self._comment(self.note, self.member, 'Rechazado', Comment.Status.REJECTED)
        reply = self._comment(
            self.note, self.other, 'Respuesta visible', Comment.Status.VISIBLE, visible,
        )
        self._comment(
            self.note, self.other, 'Respuesta oculta', Comment.Status.PENDING, visible,
        )

        response = self.client.get(f'/notes/{self.note.id}/comments/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item['id'] for item in response.data], [visible.id])
        self.assertEqual(
            [item['id'] for item in response.data[0]['replies']],
            [reply.id],
        )
        rendered = str(response.data)
        self.assertNotIn('Pendiente', rendered)
        self.assertNotIn('Rechazado', rendered)
        self.assertNotIn('Respuesta oculta', rendered)

    def test_reply_must_target_a_top_level_comment_on_the_same_note(self):
        self._token(self.member)
        top = self.client.post(
            f'/notes/{self.note.id}/comments/',
            {'body': 'Comentario de primer nivel'},
            format='json',
        )
        reply = self.client.post(
            f'/notes/{self.note.id}/comments/',
            {'body': 'Respuesta directa', 'parent': top.data['id']},
            format='json',
        )
        nested = self.client.post(
            f'/notes/{self.note.id}/comments/',
            {'body': 'Tercer nivel', 'parent': reply.data['id']},
            format='json',
        )
        other_parent = self._comment(
            self.other_note, self.member, 'Otra nota', Comment.Status.VISIBLE,
        )
        cross = self.client.post(
            f'/notes/{self.note.id}/comments/',
            {'body': 'Cruce de nota', 'parent': other_parent.id},
            format='json',
        )
        self._token(self.editor)
        editor_reply = self.client.post(
            f'/notes/{self.note.id}/comments/',
            {'body': 'Respuesta del editor', 'parent': top.data['id']},
            format='json',
        )

        self.assertEqual(top.status_code, status.HTTP_201_CREATED)
        self.assertEqual(reply.status_code, status.HTTP_201_CREATED)
        self.assertEqual(reply.data['parent'], top.data['id'])
        self.assertEqual(reply.data['status'], Comment.Status.PENDING)
        self.assertEqual(nested.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(cross.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(editor_reply.status_code, status.HTTP_201_CREATED)
        self.assertEqual(editor_reply.data['nickname'], 'editor_demo')

    def test_empty_or_oversized_body_is_rejected(self):
        self._token(self.member)
        for body in ('', '   ', 'a' * 1001):
            response = self.client.post(
                f'/notes/{self.note.id}/comments/',
                {'body': body},
                format='json',
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        accepted = self.client.post(
            f'/notes/{self.note.id}/comments/',
            {'body': 'a' * 1000},
            format='json',
        )
        self.assertEqual(accepted.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 1)

    def test_visitor_can_read_visible_comments_but_cannot_post(self):
        visible = self._comment(
            self.note, self.member, 'Visible', Comment.Status.VISIBLE,
        )
        listed = self.client.get(f'/notes/{self.note.id}/comments/')
        posted = self.client.post(
            f'/notes/{self.note.id}/comments/',
            {'body': 'No autenticado'},
            format='json',
        )

        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertEqual(listed.data[0]['id'], visible.id)
        self.assertEqual(posted.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Comment.objects.count(), 1)

    def test_author_updates_or_deletes_only_their_pending_comment(self):
        self._token(self.member)
        created = self.client.post(
            f'/notes/{self.note.id}/comments/',
            {'body': 'Texto original'},
            format='json',
        )
        comment_id = created.data['id']
        updated = self.client.patch(
            f'/comments/{comment_id}/',
            {'body': 'Texto editado', 'nickname': 'hack', 'status': 'visible'},
            format='json',
        )
        comment = Comment.objects.get(pk=comment_id)
        self._token(self.other)
        forbidden_edit = self.client.patch(
            f'/comments/{comment_id}/',
            {'body': 'Ajeno'},
            format='json',
        )
        forbidden_delete = self.client.delete(f'/comments/{comment_id}/')
        self._token(self.editor)
        self.client.post(
            f'/comments/{comment_id}/moderate/',
            {'status': Comment.Status.VISIBLE},
            format='json',
        )
        self._token(self.member)
        edit_visible = self.client.patch(
            f'/comments/{comment_id}/',
            {'body': 'Ya no'},
            format='json',
        )
        delete_visible = self.client.delete(f'/comments/{comment_id}/')
        self._token(self.member)
        pending = self.client.post(
            f'/notes/{self.note.id}/comments/',
            {'body': 'Se puede borrar'},
            format='json',
        )
        deleted = self.client.delete(f'/comments/{pending.data["id"]}/')

        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertEqual(comment.body, 'Texto editado')
        self.assertEqual(comment.nickname, 'miembro_uno')
        self.assertEqual(comment.status, Comment.Status.PENDING)
        self.assertEqual(forbidden_edit.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(forbidden_delete.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(edit_visible.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(delete_visible.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comment.objects.filter(pk=pending.data['id']).exists())

    def test_member_can_report_a_comment_only_once_while_open(self):
        comment = self._comment(
            self.note, self.other, 'Visible', Comment.Status.VISIBLE,
        )
        self._token(self.member)
        first = self.client.post(f'/comments/{comment.id}/reports/', {}, format='json')
        second = self.client.post(f'/comments/{comment.id}/reports/', {}, format='json')
        self.client.credentials()
        visitor = self.client.post(f'/comments/{comment.id}/reports/', {}, format='json')

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            CommentReport.objects.filter(
                comment=comment,
                reporter=self.member,
                status=CommentReport.Status.OPEN,
            ).count(),
            1,
        )
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(visitor.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_only_editor_or_moderator_records_a_moderation_action(self):
        comment = self._comment(
            self.note, self.member, 'Por revisar', Comment.Status.PENDING,
        )
        self._token(self.member)
        denied = self.client.post(
            f'/comments/{comment.id}/moderate/',
            {'status': Comment.Status.VISIBLE},
            format='json',
        )
        self._token(self.editor)
        visible = self.client.post(
            f'/comments/{comment.id}/moderate/',
            {'status': Comment.Status.VISIBLE},
            format='json',
        )
        comment.refresh_from_db()
        action = ModerationAction.objects.get(comment=comment, status=Comment.Status.VISIBLE)
        self._token(self.moderator)
        rejected = self.client.post(
            f'/comments/{comment.id}/moderate/',
            {'status': Comment.Status.REJECTED},
            format='json',
        )
        invalid = self.client.post(
            f'/comments/{comment.id}/moderate/',
            {'status': Comment.Status.PENDING},
            format='json',
        )
        comment.refresh_from_db()

        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(visible.status_code, status.HTTP_200_OK)
        self.assertEqual(action.actor, self.editor)
        self.assertEqual(action.comment, comment)
        self.assertEqual(rejected.status_code, status.HTTP_200_OK)
        self.assertEqual(comment.status, Comment.Status.REJECTED)
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            ModerationAction.objects.filter(comment=comment).count(),
            2,
        )

    def test_member_cannot_read_comments_on_a_draft_note(self):
        draft = Note.objects.create(
            title='Borrador',
            content='Oculto.',
            source=self.source,
        )
        self._token(self.member)
        listed = self.client.get(f'/notes/{draft.id}/comments/')
        posted = self.client.post(
            f'/notes/{draft.id}/comments/',
            {'body': 'No debe verse'},
            format='json',
        )

        self.assertEqual(listed.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(posted.status_code, status.HTTP_404_NOT_FOUND)
