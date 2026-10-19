from django.contrib import admin

from .models import (
    AsignacionDistritoJudicial,
    CircuitoJudicial,
    DistritoFederalElectoral,
    DistritoJudicialElectoral,
    Entidad,
    Localidad,
    ManzanaGeoelectoral,
    Municipio,
    NoteMention,
    SeccionElectoral,
)


@admin.register(Entidad)
class EntidadAdmin(admin.ModelAdmin):
    list_display = ('clave', 'nombre', 'fuente')
    search_fields = ('nombre',)


@admin.register(DistritoFederalElectoral)
class DistritoFederalElectoralAdmin(admin.ModelAdmin):
    list_display = ('entidad', 'numero', 'fuente')
    list_filter = ('entidad',)


@admin.register(CircuitoJudicial)
class CircuitoJudicialAdmin(admin.ModelAdmin):
    list_display = ('entidad', 'numero', 'romano', 'nombre')


@admin.register(DistritoJudicialElectoral)
class DistritoJudicialElectoralAdmin(admin.ModelAdmin):
    list_display = ('entidad', 'numero', 'fuente')
    list_filter = ('entidad',)


@admin.register(Municipio)
class MunicipioAdmin(admin.ModelAdmin):
    list_display = ('entidad', 'clave', 'nombre')
    search_fields = ('nombre',)


@admin.register(SeccionElectoral)
class SeccionElectoralAdmin(admin.ModelAdmin):
    list_display = ('entidad', 'numero', 'municipio', 'tipo_nombre', 'distrito_federal')
    search_fields = ('numero',)


@admin.register(AsignacionDistritoJudicial)
class AsignacionDistritoJudicialAdmin(admin.ModelAdmin):
    list_display = ('seccion', 'distrito_judicial', 'circuito', 'vigencia')


@admin.register(Localidad)
class LocalidadAdmin(admin.ModelAdmin):
    list_display = ('municipio', 'clave', 'nombre', 'tipo_nombre')
    search_fields = ('nombre',)


@admin.register(ManzanaGeoelectoral)
class ManzanaGeoelectoralAdmin(admin.ModelAdmin):
    list_display = ('seccion', 'localidad', 'clave', 'status')


@admin.register(NoteMention)
class NoteMentionAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'note')
    search_fields = ('candidate__name', 'note__title')
    autocomplete_fields = ('candidate', 'note')
