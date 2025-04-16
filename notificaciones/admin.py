from django.contrib import admin
from .models import Notificacion

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = (
        'asunto',
        'funcionario',
        'funcionario_cc',
        'tipo_notificacion',
        'enviado',
        'fecha_hora_envio',
    )
    list_filter = ('tipo_notificacion', 'enviado', 'fecha_hora_envio')
    search_fields = ('asunto', 'mensaje', 'funcionario__nombre', 'funcionario__apellido', 'funcionario_cc__nombre')
    date_hierarchy = 'fecha_hora_envio'
    readonly_fields = ('fecha_hora_envio',)

    fieldsets = (
        (None, {
            'fields': ('asunto', 'mensaje', 'tipo_notificacion', 'enviado')
        }),
        ('Relacionados', {
            'fields': ('funcionario', 'funcionario_cc', 'solicitud_vacaciones', 'reintegro_vacaciones')
        }),
        ('Metadatos', {
            'fields': ('fecha_hora_envio',)
        }),
    )
