from django.contrib.auth.models import User
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Candidacy,
    Candidate,
    Comment,
    CommentReport,
    Election,
    ElectionZone,
    ModerationAction,
    Note,
    Office,
    PostalCode,
    PostalCodeZoneMapping,
    ProfileNicknameError,
    Source,
    Tag,
    ensure_user_profile,
)
from .permissions import (
    IsEditor,
    IsMemberOrEditor,
    user_can_moderate,
    user_in_group,
    user_is_editor,
)
from .serializers import (
    CandidacySerializer,
    CandidateSerializer,
    CommentCreateSerializer,
    CommentReadSerializer,
    CommentUpdateSerializer,
    ElectionSerializer,
    ElectionZoneSerializer,
    NoteSerializer,
    OfficeSerializer,
    PostalCodeSerializer,
    PostalCodeZoneMappingSerializer,
    RegisterSerializer,
    SourceSerializer,
    TagSerializer,
)


def _user_for_login(email, username):
    if email:
        lookup = {'email__iexact': str(email)}
    elif username:
        lookup = {'username__iexact': str(username)}
    else:
        return None
    try:
        return User.objects.get(**lookup)
    except (User.DoesNotExist, User.MultipleObjectsReturned):
        return None


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
            try:
                user = serializer.save()
            except serializers.ValidationError as exc:
                return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
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
        user = _user_for_login(email, username)
        if (
            user is None
            or not user.is_active
            or not user.check_password(password)
        ):
            return Response(
                {'detail': 'Credenciales inválidas.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            ensure_user_profile(user)
        except ProfileNicknameError as exc:
            return Response(
                {'detail': exc.message},
                status=status.HTTP_400_BAD_REQUEST,
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
        try:
            ensure_user_profile(user)
        except ProfileNicknameError as exc:
            return Response(
                {'detail': exc.message},
                status=status.HTTP_400_BAD_REQUEST,
            )
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


class EditorWriteMixin:
    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsEditor()]
        return [permissions.AllowAny()]


class ElectionViewSet(EditorWriteMixin, viewsets.ModelViewSet):
    queryset = Election.objects.all()
    serializer_class = ElectionSerializer


class OfficeViewSet(EditorWriteMixin, viewsets.ModelViewSet):
    queryset = Office.objects.all()
    serializer_class = OfficeSerializer


class CandidateViewSet(EditorWriteMixin, viewsets.ModelViewSet):
    queryset = Candidate.objects.all()
    serializer_class = CandidateSerializer


class ElectionZoneViewSet(EditorWriteMixin, viewsets.ModelViewSet):
    queryset = ElectionZone.objects.all()
    serializer_class = ElectionZoneSerializer


class PostalCodeViewSet(EditorWriteMixin, viewsets.ModelViewSet):
    queryset = PostalCode.objects.all()
    serializer_class = PostalCodeSerializer


class CandidacyViewSet(EditorWriteMixin, viewsets.ModelViewSet):
    serializer_class = CandidacySerializer

    def get_queryset(self):
        queryset = Candidacy.objects.all()
        if self.request.query_params.get('applicable') == 'true':
            queryset = queryset.filter(status=Candidacy.Status.CONFIRMED)
        return queryset


class PostalCodeZoneMappingViewSet(EditorWriteMixin, viewsets.ModelViewSet):
    queryset = PostalCodeZoneMapping.objects.all()
    serializer_class = PostalCodeZoneMappingSerializer


class PostalCodeSearchView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, format=None):
        code = str(request.query_params.get('code') or '').strip()
        if not code:
            return Response(
                {'detail': 'Indica un código postal.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        mappings = PostalCodeZoneMapping.objects.filter(
            postal_code__code=code,
        ).select_related('zone')
        if not mappings.exists():
            return Response({
                'code': code,
                'zones': [],
                'detail': (
                    'No hay zonas oficiales registradas para este código postal.'
                ),
            })
        zones = []
        for mapping in mappings:
            applicable = Candidacy.objects.filter(
                zone=mapping.zone,
                status=Candidacy.Status.CONFIRMED,
            )
            zones.append({
                'id': mapping.zone_id,
                'name': mapping.zone.name,
                'code': mapping.zone.code,
                'valid_from': mapping.valid_from.isoformat(),
                'valid_to': mapping.valid_to.isoformat(),
                'source': mapping.source,
                'applicable_candidacies': CandidacySerializer(
                    applicable,
                    many=True,
                ).data,
            })
        return Response({'code': code, 'zones': zones})