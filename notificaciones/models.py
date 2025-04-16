from django.db import models
from usuarios.models import Funcionario
from vacaciones.models import SolicitudVacaciones, ReintegroVacaciones

class Notificacion(models.Model):
    TIPO_NOTIFICACION_CHOICES = [
        ('solicitud', 'Solicitud'),
        ('reintegro', 'Reintegro')
    ]

    asunto = models.CharField("Asunto", max_length=150)
    mensaje = models.TextField("Mensaje")
    fecha_hora_envio = models.DateTimeField("Fecha y hora de envío", auto_now_add=True)
    enviado = models.BooleanField("¿Enviado?", default=False)

    funcionario = models.ForeignKey(Funcionario, verbose_name="Funcionario destinatario", on_delete=models.CASCADE, related_name="notificaciones_recibidas")
    funcionario_cc = models.ForeignKey(Funcionario, verbose_name="Funcionario CC", on_delete=models.SET_NULL, null=True, blank=True, related_name="notificaciones_copia")
    solicitud_vacaciones = models.ForeignKey(SolicitudVacaciones, null=True, blank=True, on_delete=models.CASCADE, verbose_name="Solicitud relacionada")
    reintegro_vacaciones = models.ForeignKey(ReintegroVacaciones, null=True, blank=True, on_delete=models.CASCADE, verbose_name="Reintegro relacionado")
    tipo_notificacion = models.CharField("Tipo de notificación", max_length=20, choices=TIPO_NOTIFICACION_CHOICES)

    def save(self, *args, **kwargs):
        if self.tipo_notificacion == 'solicitud':
            self.reintegro_vacaciones = None
        elif self.tipo_notificacion == 'reintegro':
            self.solicitud_vacaciones = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.asunto} - {self.funcionario}"

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
