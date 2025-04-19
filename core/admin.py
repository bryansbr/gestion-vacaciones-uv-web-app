from django.contrib import admin
from .models import Estamento, FacultadDependencia, Sede

@admin.register(Estamento)
class EstamentoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)
    list_filter = ('nombre',)

@admin.register(FacultadDependencia)
class FacultadDependenciaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)
    list_filter = ('nombre',)

@admin.register(Sede)
class SedeAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'direccion')
    search_fields = ('nombre', 'direccion')
    list_filter = ('nombre',)
