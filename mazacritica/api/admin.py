from django.contrib import admin

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
    Source,
    Tag,
    UserProfile,
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('nickname', 'user')
    search_fields = ('nickname', 'user__email', 'user__username')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'kind', 'is_active')
    list_filter = ('kind', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'publisher', 'published_at', 'url')
    search_fields = ('name', 'publisher', 'url')
    list_filter = ('publisher',)


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'held_on')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ('name', 'power')
    list_filter = ('power',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ElectionZone)
class ElectionZoneAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')


@admin.register(PostalCode)
class PostalCodeAdmin(admin.ModelAdmin):
    list_display = ('code',)
    search_fields = ('code',)


@admin.register(Candidacy)
class CandidacyAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'election', 'office', 'zone', 'status')
    list_filter = ('status', 'office__power')


@admin.register(PostalCodeZoneMapping)
class PostalCodeZoneMappingAdmin(admin.ModelAdmin):
    list_display = ('postal_code', 'zone', 'source', 'valid_from', 'valid_to')
    search_fields = ('postal_code__code', 'zone__code', 'source')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('nickname', 'note', 'status', 'parent', 'created_at')
    list_filter = ('status',)
    search_fields = ('nickname', 'body')


@admin.register(CommentReport)
class CommentReportAdmin(admin.ModelAdmin):
    list_display = ('comment', 'reporter', 'status', 'created_at')
    list_filter = ('status',)


@admin.register(ModerationAction)
class ModerationActionAdmin(admin.ModelAdmin):
    list_display = ('comment', 'actor', 'status', 'created_at')
    list_filter = ('status',)


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'source', 'published_at', 'author')
    list_filter = ('status', 'tags', 'source')
    search_fields = ('title', 'excerpt', 'content')
    filter_horizontal = ('tags',)
    prepopulated_fields = {'slug': ('title',)}
