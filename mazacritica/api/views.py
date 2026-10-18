from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework import permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Note, Source, Tag
from .permissions import IsEditor, user_is_editor
from .serializers import (
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