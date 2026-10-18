from django.contrib.auth.models import User
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Comment, CommentReport, ModerationAction, Note, Source, Tag
from .permissions import (
    IsEditor,
    IsMemberOrEditor,
    user_can_moderate,
    user_in_group,
    user_is_editor,
)
from .serializers import (
    CommentCreateSerializer,
    CommentReadSerializer,
    CommentUpdateSerializer,
    NoteSerializer,
    RegisterSerializer,
    SourceSerializer,
    TagSerializer,
)


def _account_payload(user, token):
    return {
        'token': token.key,
        'nickname': user.profile.nickname,
        'email': user.email,
        'groups': list(user.groups.order_by('name').values_list('name', flat=True)),
    }


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, format=None):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    'id': user.id,
                    'email': user.email,
                    'nickname': user.profile.nickname,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, format=None):
        email = request.data.get('email')
        username = request.data.get('username')
        password = request.data.get('password') or ''
        user = None
        if email:
            user = User.objects.filter(email__iexact=str(email)).first()
        elif username:
            user = User.objects.filter(username__iexact=str(username)).first()
        if (
            user is None
            or not user.is_active
            or not user.check_password(password)
        ):
            return Response(
                {'detail': 'Credenciales inválidas.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        token, _created = Token.objects.get_or_create(user=user)
        return Response(_account_payload(user, token))


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        return Response({
            'id': user.id,
            'email': user.email,
            'nickname': user.profile.nickname,
            'groups': list(
                user.groups.order_by('name').values_list('name', flat=True)
            ),
        })


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsEditor()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        queryset = super().get_queryset()
        active = self.request.query_params.get('active')
        if active == 'true':
            queryset = queryset.filter(is_active=True)
        elif active == 'false':
            queryset = queryset.filter(is_active=False)
        return queryset


class SourceViewSet(viewsets.ModelViewSet):
    queryset = Source.objects.all()
    serializer_class = SourceSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsEditor()]
        return [permissions.AllowAny()]


class NoteViewSet(viewsets.ModelViewSet):
    serializer_class = NoteSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsEditor()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        queryset = Note.objects.select_related(
            'source',
            'author',
        ).prefetch_related('tags')
        editor = user_is_editor(self.request.user)
        if not editor:
            queryset = queryset.filter(status=Note.EditorialStatus.PUBLISHED)

        tag = self.request.query_params.get('tag')
        if tag:
            queryset = queryset.filter(
                Q(tags__slug=tag) | Q(tags__name__iexact=tag)
            )

        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(published_at__date__gte=date_from)

        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(published_at__date__lte=date_to)

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(excerpt__icontains=search)
                | Q(content__icontains=search)
            )
        return queryset.distinct()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


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