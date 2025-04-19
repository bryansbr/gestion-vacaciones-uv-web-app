from django.contrib import admin
from .models import (
    PeriodoVacacional,
    SolicitudVacaciones,
    DiasPendientesVacaciones,
    ReintegroVacaciones,
    HistoricoAcciones
)

@admin.register(PeriodoVacacional)
class PeriodoVacacionalAdmin(admin.ModelAdmin):
    list_display = ('id', 'funcionario', 'fecha_inicio_periodo', 'fecha_fin_periodo', 'dias_totales_periodo')
    search_fields = ('funcionario__nombre', 'funcionario__apellido')
    list_filter = ('fecha_inicio_periodo', 'fecha_fin_periodo')

@admin.register(SolicitudVacaciones)
class SolicitudVacacionesAdmin(admin.ModelAdmin):
    list_display = ('codigo_sabs', 'funcionario', 'fecha_inicio_vacaciones', 'fecha_fin_vacaciones', 'estado_solicitud')
    search_fields = ('codigo_sabs', 'funcionario__nombre', 'funcionario__apellido')
    list_filter = ('estado_solicitud', 'mes_pago', 'anio_pago')

@admin.register(DiasPendientesVacaciones)
class DiasPendientesVacacionesAdmin(admin.ModelAdmin):
    list_display = ('id', 'solicitud_vacaciones', 'periodo_desde', 'periodo_hasta', 'dias_a_disfrutar')
    search_fields = ('solicitud_vacaciones__codigo_sabs',)

@admin.register(ReintegroVacaciones)
class ReintegroVacacionesAdmin(admin.ModelAdmin):
    list_display = ('codigo_sabs', 'funcionario', 'fecha_reintegro', 'estado_solicitud')
    search_fields = ('codigo_sabs', 'funcionario__nombre', 'funcionario__apellido')
    list_filter = ('estado_solicitud', 'fecha_reintegro')

@admin.register(HistoricoAcciones)
class HistoricoAccionesAdmin(admin.ModelAdmin):
    list_display = ('id', 'accion_realizada', 'tipo_accion', 'usuario', 'fecha_hora_accion', 'grupo_autorizador')
    list_filter = ('tipo_accion', 'accion_realizada', 'grupo_autorizador')
    search_fields = ('usuario__email',)
