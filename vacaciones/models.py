from django.db import models
#from usuarios.models import Funcionario
#from core.models import Catalogo

"""
class PeriodoVacacional(models.Model):
    fecha_inicio_periodo = models.DateField()
    fecha_fin_periodo = models.DateField()
    dias_totales_periodo = models.IntegerField()
    dias_pendientes_periodo = models.IntegerField()
    dias_disfrutados_periodo = models.IntegerField(default=0)

    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE)

class SolicitudVacaciones(models.Model):
    TIPO_DIAS = (('H', 'Hábiles'), ('C', 'Calendario'))

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
    estado_solicitud = models.ForeignKey(Catalogo, on_delete=models.PROTECT, related_name='solicitudes_estado')

class DiasPendientesVacaciones(models.Model):
    periodo_desde = models.IntegerField()
    periodo_hasta = models.IntegerField()
    dias_a_disfrutar = models.IntegerField()
    dias_pendientes = models.IntegerField()
    fecha_disfrute_desde = models.DateField()
    fecha_disfrute_hasta = models.DateField()

    solicitud_vacaciones = models.ForeignKey(SolicitudVacaciones, on_delete=models.CASCADE)

class ReintegroVacaciones(models.Model):
    TIPO_DIAS = (('H', 'Hábiles'), ('C', 'Calendario'))
    MOTIVOS_REINTEGRO = [('Vacaciones', 'Vacaciones')]

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
    estado_solicitud = models.ForeignKey(Catalogo, on_delete=models.PROTECT, related_name='reintegros_estado')

class HistoricoAcciones(models.Model):
    TIPO_ACCION = [('solicitud', 'Solicitud'), ('reintegro', 'Reintegro')]

    accion_realizada = models.CharField(max_length=50)
    fecha_hora_accion = models.DateTimeField(auto_now_add=True)
    observacion = models.TextField(blank=True, null=True)

    solicitud_vacaciones = models.ForeignKey(SolicitudVacaciones, null=True, blank=True, on_delete=models.CASCADE)
    reintegro_vacaciones = models.ForeignKey(ReintegroVacaciones, null=True, blank=True, on_delete=models.CASCADE)
    tipo_accion = models.CharField(max_length=20, choices=TIPO_ACCION)

    def save(self, *args, **kwargs):
        if self.tipo_accion == 'solicitud':
            self.reintegro_vacaciones = None
        elif self.tipo_accion == 'reintegro':
            self.solicitud_vacaciones = None
        super().save(*args, **kwargs)
"""
