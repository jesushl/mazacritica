from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import Comment, CommentReport, ModerationAction, Note
from api.permissions import IsMemberOrEditor, user_can_moderate, user_in_group, user_is_editor
from api.serializers.comments import (
    CommentCreateSerializer,
    CommentReadSerializer,
    CommentUpdateSerializer,
)

def get_comment_note(request, note_id):
    note = get_object_or_404(Note, pk=note_id)
    if (
        note.status != Note.EditorialStatus.PUBLISHED
        and not user_is_editor(request.user)
    ):
        raise Http404
    return note


class NoteCommentListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsMemberOrEditor()]
        return [permissions.AllowAny()]

    def get(self, request, note_id, format=None):
        note = get_comment_note(request, note_id)
        comments = Comment.objects.filter(
            note=note,
            parent__isnull=True,
            status=Comment.Status.VISIBLE,
        ).prefetch_related('replies')
        return Response(CommentReadSerializer(comments, many=True).data)

    def post(self, request, note_id, format=None):
        note = get_comment_note(request, note_id)
        serializer = CommentCreateSerializer(
            data=request.data,
            context={'note': note, 'request': request},
        )
        if serializer.is_valid():
            comment = serializer.save()
            return Response(
                CommentReadSerializer(comment).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _own_pending(self, request, comment_id):
        comment = get_object_or_404(Comment, pk=comment_id)
        if (
            comment.author_id != request.user.id
            or comment.status != Comment.Status.PENDING
        ):
            return None, Response(
                {'detail': 'Solo puedes modificar tu comentario pendiente.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return comment, None

    def patch(self, request, comment_id, format=None):
        comment, denied = self._own_pending(request, comment_id)
        if denied is not None:
            return denied
        serializer = CommentUpdateSerializer(
            comment,
            data=request.data,
            partial=True,
        )
        if serializer.is_valid():
            serializer.save()
            return Response(CommentReadSerializer(comment).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, comment_id, format=None):
        comment, denied = self._own_pending(request, comment_id)
        if denied is not None:
            return denied
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommentReportCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, comment_id, format=None):
        if not user_in_group(request.user, 'member'):
            return Response(
                {'detail': 'Solo un miembro puede reportar un comentario.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        comment = get_object_or_404(Comment, pk=comment_id)
        if CommentReport.objects.filter(
            comment=comment,
            reporter=request.user,
            status=CommentReport.Status.OPEN,
        ).exists():
            return Response(
                {'detail': 'Ya existe un reporte abierto para este comentario.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        report = CommentReport.objects.create(
            comment=comment,
            reporter=request.user,
        )
        return Response(
            {
                'id': report.id,
                'comment': comment.id,
                'reporter': request.user.id,
                'status': report.status,
            },
            status=status.HTTP_201_CREATED,
        )


class CommentModerateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, comment_id, format=None):
        if not user_can_moderate(request.user):
            return Response(
                {'detail': 'Solo un editor o moderador puede moderar.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        new_status = request.data.get('status')
        allowed = {
            ModerationAction.Status.VISIBLE,
            ModerationAction.Status.REJECTED,
        }
        if new_status not in allowed:
            return Response(
                {'status': 'El estado debe ser visible o rejected.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        comment = get_object_or_404(Comment, pk=comment_id)
        comment.status = new_status
        comment.save(update_fields=['status', 'updated_at'])
        action = ModerationAction.objects.create(
            comment=comment,
            actor=request.user,
            status=new_status,
        )
        return Response({
            'id': action.id,
            'comment': comment.id,
            'actor': request.user.id,
            'status': action.status,
        })
