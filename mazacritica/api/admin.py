from django.contrib import admin

from .models import (
    Comment,
    CommentReport,
    ModerationAction,
    Note,
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
