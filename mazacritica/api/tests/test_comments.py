from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from api.models import Comment, CommentReport, ModerationAction, Note, Source

from .helpers import create_group_user

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
        return create_group_user(
            nickname,
            email,
            'password-segura',
            group_name,
            nickname=nickname,
        )

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
