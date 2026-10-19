from django.db.models import Q
from rest_framework import permissions, viewsets

from api.models import Note, Source, Tag
from api.permissions import IsEditor, user_is_editor
from api.serializers.notes import NoteSerializer, SourceSerializer, TagSerializer

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
