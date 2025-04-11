from django.db import models
#from usuarios.models import Funcionario
#from vacaciones.models import SolicitudVacaciones, ReintegroVacaciones

"""
class Notificacion(models.Model):
    TIPO_NOTIFICACION = [('solicitud', 'Solicitud'), ('reintegro', 'Reintegro')]

    asunto = models.CharField(max_length=150)
    mensaje = models.TextField()
    fecha_hora_envio = models.DateTimeField(auto_now_add=True)
    enviado = models.BooleanField(default=False)

    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE)
    solicitud_vacaciones = models.ForeignKey(SolicitudVacaciones, null=True, blank=True, on_delete=models.CASCADE)
    reintegro_vacaciones = models.ForeignKey(ReintegroVacaciones, null=True, blank=True, on_delete=models.CASCADE)
    tipo_notificacion = models.CharField(max_length=20, choices=TIPO_NOTIFICACION)

    def save(self, *args, **kwargs):
        if self.tipo_notificacion == 'solicitud':
            self.reintegro_vacaciones = None
        elif self.tipo_notificacion == 'reintegro':
            self.solicitud_vacaciones = None
        super().save(*args, **kwargs)
"""
