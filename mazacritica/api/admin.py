from django.contrib import admin

from .models import Note, Source, Tag


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


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'source', 'published_at', 'author')
    list_filter = ('status', 'tags', 'source')
    search_fields = ('title', 'excerpt', 'content')
    filter_horizontal = ('tags',)
    prepopulated_fields = {'slug': ('title',)}
