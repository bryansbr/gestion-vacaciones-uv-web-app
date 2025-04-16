from django.db import models
from usuarios.models import Funcionario, CustomUser

class PeriodoVacacional(models.Model):
    fecha_inicio_periodo = models.DateField()
    fecha_fin_periodo = models.DateField()
    dias_totales_periodo = models.IntegerField()
    dias_pendientes_periodo = models.IntegerField()
    dias_disfrutados_periodo = models.IntegerField(default=0)

    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE)

    def __str__(self):
        return f"Periodo {self.fecha_inicio_periodo} - {self.fecha_fin_periodo} ({self.funcionario})"

    class Meta:
        verbose_name = "Periodo vacacional"
        verbose_name_plural = "Periodos vacacionales"

class SolicitudVacaciones(models.Model):
    TIPO_DIAS = (('H', 'Hábiles'), ('C', 'Calendario'))
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('en_revision', 'En revisión'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('cancelado', 'Cancelado')
    ]

    codigo_sabs = models.CharField(max_length=50, unique=True)
    fecha_elaboracion = models.DateField(auto_now_add=True)
    fecha_inicio_vacaciones = models.DateField()
    fecha_fin_vacaciones = models.DateField()
    total_dias_solicitados = models.IntegerField()
    tipo_dias_solicitados = models.CharField(max_length=1, choices=TIPO_DIAS)
    quincena_pago = models.IntegerField(choices=[(1, 'Primera'), (2, 'Segunda')])
    mes_pago = models.IntegerField()
    anio_pago = models.IntegerField()
    observaciones = models.TextField(blank=True, null=True)
    disfrute_dias_pendientes = models.BooleanField(default=False)

    periodo_vacacional = models.ForeignKey(PeriodoVacacional, on_delete=models.PROTECT)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE)
    estado_solicitud = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')

    def __str__(self):
        return f"Solicitud {self.codigo_sabs} - {self.funcionario}"
    
    class Meta:
        verbose_name = "Solicitud de vacaciones"
        verbose_name_plural = "Solicitudes de vacaciones"

class DiasPendientesVacaciones(models.Model):
    periodo_desde = models.IntegerField()
    periodo_hasta = models.IntegerField()
    dias_a_disfrutar = models.IntegerField()
    dias_pendientes = models.IntegerField()
    fecha_disfrute_desde = models.DateField()
    fecha_disfrute_hasta = models.DateField()

    solicitud_vacaciones = models.ForeignKey(SolicitudVacaciones, on_delete=models.CASCADE)

    def __str__(self):
        return f"Días pendientes {self.solicitud_vacaciones.codigo_sabs}"
    
    class Meta:
        verbose_name = "Días pendientes de vacaciones"
        verbose_name_plural = "Días pendientes de vacaciones"

class ReintegroVacaciones(models.Model):
    TIPO_DIAS = (('H', 'Hábiles'), ('C', 'Calendario'))
    MOTIVOS_REINTEGRO = [('Vacaciones', 'Vacaciones')]
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('en_revision', 'En revisión'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('cancelado', 'Cancelado')
    ]

    codigo_sabs = models.CharField(max_length=50, unique=True)
    fecha_elaboracion = models.DateField(auto_now_add=True)
    fecha_reintegro = models.DateField()
    motivo_reintegro = models.CharField(max_length=50, choices=MOTIVOS_REINTEGRO)
    observaciones = models.TextField(blank=True, null=True)
    fecha_disfrute_desde = models.DateField()
    fecha_disfrute_hasta = models.DateField()
    dias_disfrutados = models.IntegerField()
    tipo_dias_disfrutados = models.CharField(max_length=1, choices=TIPO_DIAS)
    dias_pendientes = models.IntegerField()
    tipo_dias_pendientes = models.CharField(max_length=1, choices=TIPO_DIAS)

    periodo_vacacional = models.ForeignKey(PeriodoVacacional, on_delete=models.PROTECT)
    solicitud_vacaciones = models.ForeignKey(SolicitudVacaciones, on_delete=models.PROTECT)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE)
    estado_solicitud = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')

    def __str__(self):
        return f"Reintegro {self.codigo_sabs} - {self.funcionario}"
    
    class Meta:
        verbose_name = "Reintegro de vacaciones"
        verbose_name_plural = "Reintegros de vacaciones"

class HistoricoAcciones(models.Model):
    TIPO_ACCION = [('solicitud', 'Solicitud'), ('reintegro', 'Reintegro')]
    ACCIONES = [
        ('creacion', 'Creación'),
        ('edicion', 'Edición'),
        ('aprobacion', 'Aprobación'),
        ('rechazo', 'Rechazo'),
        ('observacion', 'Observación'),
        ('cancelacion', 'Cancelación')
    ]

    accion_realizada = models.CharField(max_length=50, choices=ACCIONES)
    fecha_hora_accion = models.DateTimeField(auto_now_add=True)
    observacion = models.TextField(blank=True, null=True)
    tipo_accion = models.CharField(max_length=20, choices=TIPO_ACCION)

    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    solicitud_vacaciones = models.ForeignKey(SolicitudVacaciones, null=True, blank=True, on_delete=models.CASCADE)
    reintegro_vacaciones = models.ForeignKey(ReintegroVacaciones, null=True, blank=True, on_delete=models.CASCADE)
    grupo_autorizador = models.CharField(max_length=50, blank=True, null=True)
    nuevo_estado = models.CharField(max_length=20, blank=True, null=True)
    estado_anterior = models.CharField(max_length=20, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.tipo_accion == 'solicitud':
            self.reintegro_vacaciones = None
        elif self.tipo_accion == 'reintegro':
            self.solicitud_vacaciones = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tipo_accion} - {self.accion_realizada} por {self.usuario}"
    
    class Meta:
        verbose_name = "Historial de acciones"
        verbose_name_plural = "Historial de acciones"
