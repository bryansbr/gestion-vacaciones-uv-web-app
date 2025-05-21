from datetime import timedelta, datetime
from django.db import models
from django.core.exceptions import ValidationError
from usuarios.models import Funcionario, CustomUser
import holidays

# -----------------------------------------
# MODELO: PeriodoVacacional
# -----------------------------------------
class PeriodoVacacional(models.Model):
    fecha_inicio_periodo = models.DateField(verbose_name="Fecha de inicio del periodo")
    fecha_fin_periodo = models.DateField(verbose_name="Fecha de fin del periodo")
    dias_totales_periodo = models.IntegerField(verbose_name="Días totales del periodo", default=0, editable=False)
    dias_pendientes_periodo = models.IntegerField(verbose_name="Días pendientes del periodo", default=0, editable=False)
    dias_disfrutados_periodo = models.IntegerField(verbose_name="Días disfrutados del periodo", default=0)

    funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.CASCADE,
        related_name="periodos_vacacionales",
        verbose_name="Funcionario"
    )

    def _calcular_dias_docente_1279(self, inicio, fin, festivos):
        dias_habiles, actual = 0, inicio
        while actual <= fin and dias_habiles < 15:
            if actual.weekday() < 5 and actual not in festivos:
                dias_habiles += 1
            actual += timedelta(days=1)

        dias_calendario = (fin - actual + timedelta(days=1)).days if actual <= fin else 0
        return dias_habiles + dias_calendario

    def _calcular_dias_generico(self, inicio, fin, festivos):
        total, actual = 0, inicio
        while actual <= fin:
            if actual.weekday() < 5 and actual not in festivos:
                total += 1
            actual += timedelta(days=1)
        return total

    def contar_dias_por_regimen(self):
        inicio, fin = self.fecha_inicio_periodo, self.fecha_fin_periodo
        if not inicio or not fin:
            return 0

        festivos = holidays.Colombia(years=range(inicio.year, fin.year + 1))
        estamento = self.funcionario.estamento.nombre.lower()
        decreto = (self.funcionario.decreto_resolucion or '').strip()

        if estamento == 'docente' and decreto == '1279':
            return self._calcular_dias_docente_1279(inicio, fin, festivos)
        
        return self._calcular_dias_generico(inicio, fin, festivos)

    def clean(self):
        if self.fecha_inicio_periodo > self.fecha_fin_periodo:
            raise ValidationError("La fecha de inicio no puede ser posterior a la fecha de fin.")
        self.dias_totales_periodo = self.contar_dias_por_regimen()

        if self.dias_pendientes_periodo + self.dias_disfrutados_periodo > self.dias_totales_periodo:
            raise ValidationError("La suma de días pendientes y disfrutados no puede superar los días totales.")
        periodos = PeriodoVacacional.objects.filter(funcionario=self.funcionario)
        
        if self.pk:
            periodos = periodos.exclude(pk=self.pk)

        for periodo in periodos:
            if (self.fecha_inicio_periodo <= periodo.fecha_fin_periodo <= self.fecha_fin_periodo) or \
               (periodo.fecha_inicio_periodo <= self.fecha_fin_periodo <= periodo.fecha_fin_periodo):
                raise ValidationError("Este funcionario ya tiene un periodo que se cruza con las fechas ingresadas.")

    def save(self, *args, **kwargs):
        self.dias_totales_periodo = self.contar_dias_por_regimen()
        self.dias_pendientes_periodo = self.dias_totales_periodo - self.dias_disfrutados_periodo
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Periodo {self.fecha_inicio_periodo} - {self.fecha_fin_periodo} ({self.funcionario})"

    class Meta:
        verbose_name = "Periodo vacacional"
        verbose_name_plural = "Periodos vacacionales"
        ordering = ['-fecha_inicio_periodo']

# -----------------------------------------
# MODELO: SolicitudVacaciones
# -----------------------------------------
class SolicitudVacaciones(models.Model):
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
    quincena_pago = models.IntegerField(choices=[(1, 'Primera'), (2, 'Segunda')])
    mes_pago = models.IntegerField()
    anio_pago = models.IntegerField()
    observaciones = models.TextField(blank=True, null=True)
    disfrute_dias_pendientes = models.BooleanField(default=False)

    periodo_vacacional = models.ForeignKey(PeriodoVacacional, on_delete=models.PROTECT)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE)
    estado_solicitud = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')

    def clean(self):
        errores = {}

        # Validación de antigüedad o días pendientes
        if not self.funcionario.puede_solicitar_vacaciones():
            errores['funcionario'] = "El funcionario no cumple con la antigüedad mínima ni tiene días pendientes."

        # Validación de cruce de fechas con otras solicitudes en curso
        solicitudes = SolicitudVacaciones.objects.filter(
            funcionario=self.funcionario,
            estado_solicitud__in=['aprobado', 'en_revision']
        ).exclude(pk=self.pk)

        for s in solicitudes:
            if (
                self.fecha_inicio_vacaciones <= s.fecha_fin_vacaciones and
                self.fecha_fin_vacaciones >= s.fecha_inicio_vacaciones
            ):
                errores['fecha_inicio_vacaciones'] = "Las fechas se cruzan con otra solicitud en revisión o aprobada."
                break

        # Validación de cálculo de días (solo calendario)
        if self.fecha_inicio_vacaciones and self.fecha_fin_vacaciones:
            dias_solicitados = (self.fecha_fin_vacaciones - self.fecha_inicio_vacaciones).days + 1
            if dias_solicitados != self.total_dias_solicitados:
                errores['total_dias_solicitados'] = (
                    f"Se calcularon {dias_solicitados} días calendario, pero se ingresaron {self.total_dias_solicitados}."
                )

        # Validación de días disponibles en el periodo vacacional
        if self.periodo_vacacional and self.total_dias_solicitados > self.periodo_vacacional.dias_pendientes_periodo:
            errores['periodo_vacacional'] = "No hay suficientes días pendientes disponibles en el periodo seleccionado."

        if errores:
            raise ValidationError(errores)

    def __str__(self):
        return f"Solicitud {self.codigo_sabs} - {self.funcionario}"

    class Meta:
        verbose_name = "Solicitud de vacaciones"
        verbose_name_plural = "Solicitudes de vacaciones"
        permissions = [
            ("crear_solicitud_vacaciones", "Puede crear solicitudes de vacaciones"),
            ("editar_solicitud_vacaciones", "Puede editar solicitudes de vacaciones"),
            ("ver_solicitud_vacaciones", "Puede ver solicitudes de vacaciones"),
            ("dar_visto_bueno_solicitud", "Puede dar visto bueno a solicitudes de vacaciones"),
            ("devolver_solicitud", "Puede devolver solicitudes de vacaciones para corrección"),
            ("autorizar_solicitud", "Puede autorizar solicitudes de vacaciones"),
            ("rechazar_solicitud", "Puede rechazar solicitudes de vacaciones"),
            ("cerrar_solicitud", "Puede cerrar solicitudes de vacaciones"),
        ]

    def save(self, *args, **kwargs):
        if not self.codigo_sabs:
            self.codigo_sabs = generar_codigo_sabs('VAC', datetime.now().year)
        super().save(*args, **kwargs)

# -----------------------------------------
# MODELO: DiasPendientesVacaciones
# -----------------------------------------
class DiasPendientesVacaciones(models.Model):
    periodo_desde = models.IntegerField()
    periodo_hasta = models.IntegerField()
    dias_a_disfrutar = models.IntegerField()
    dias_pendientes = models.IntegerField()
    fecha_disfrute_desde = models.DateField()
    fecha_disfrute_hasta = models.DateField()
    solicitud_vacaciones = models.ForeignKey(SolicitudVacaciones, on_delete=models.CASCADE)

    def __str__(self):
        return f"Días pendientes - {self.solicitud_vacaciones.codigo_sabs}"

    class Meta:
        verbose_name = "Días pendientes de vacaciones"
        verbose_name_plural = "Días pendientes de vacaciones"

# -----------------------------------------
# MODELO: ReintegroVacaciones
# -----------------------------------------
class ReintegroVacaciones(models.Model):
    TIPO_DIAS = (('H', 'Hábiles'), ('C', 'Calendario'))
    MOTIVOS_REINTEGRO = [('Vacaciones', 'Vacaciones')]
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('en_revision', 'En revisión'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('cancelado', 'Cancelado'),
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
    funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.CASCADE,
        related_name="reintegros_vacaciones"
    )
    estado_solicitud = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')

    def __str__(self):
        return f"Reintegro {self.codigo_sabs} - {self.funcionario}"

    class Meta:
        verbose_name = "Reintegro de vacaciones"
        verbose_name_plural = "Reintegros de vacaciones"
        permissions = [
            ("crear_reintegro_vacaciones", "Puede crear reintegros de vacaciones"),
            ("editar_reintegro_vacaciones", "Puede editar reintegros de vacaciones"),
            ("ver_reintegro_vacaciones", "Puede ver reintegros de vacaciones"),
            ("dar_visto_bueno_reintegro", "Puede dar visto bueno a reintegros de vacaciones"),
            ("devolver_reintegro", "Puede devolver reintegros para corrección"),
            ("autorizar_reintegro", "Puede autorizar reintegros de vacaciones"),
            ("rechazar_reintegro", "Puede rechazar reintegros de vacaciones"),
            ("cerrar_reintegro", "Puede cerrar reintegros de vacaciones"),
        ]

    def save(self, *args, **kwargs):
        if not self.codigo_sabs:
            self.codigo_sabs = generar_codigo_sabs('REI', datetime.now().year)
        super().save(*args, **kwargs)

# -----------------------------------------
# MODELO: HistoricoAcciones
# -----------------------------------------
class HistoricoAcciones(models.Model):
    TIPO_ACCION = [('solicitud', 'Solicitud'), ('reintegro', 'Reintegro')]
    ACCIONES = [
        ('creacion', 'Creación'),
        ('edicion', 'Edición'),
        ('aprobacion', 'Aprobación'),
        ('rechazo', 'Rechazo'),
        ('observacion', 'Observación'),
        ('cancelacion', 'Cancelación'),
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
        return f"{self.tipo_accion.capitalize()} - {self.get_accion_realizada_display()} por {self.usuario}"

    class Meta:
        verbose_name = "Historial de acciones"
        verbose_name_plural = "Historial de acciones"

def generar_codigo_sabs(tipo, anio):
    """
    Genera un código SABS único para solicitudes o reintegros.
    tipo: 'VAC' para vacaciones, 'REI' para reintegros
    anio: año actual
    """
    if tipo == 'VAC':
        modelo = SolicitudVacaciones
    else:
        modelo = ReintegroVacaciones
    
    # Obtener el último código del año actual
    ultimo_codigo = modelo.objects.filter(
        codigo_sabs__startswith=f"{tipo}-{anio}-"
    ).order_by('-codigo_sabs').first()
    
    if ultimo_codigo:
        try:
            # Extraer el número del último código, ignorando el padding
            numero_str = ultimo_codigo.codigo_sabs.split('-')[-1].lstrip('0')
            consecutivo = int(numero_str) + 1 if numero_str else 1
        except (ValueError, IndexError):
            consecutivo = 1
    else:
        consecutivo = 1
    
    padding = max(4, len(str(consecutivo)))
    return f"{tipo}{anio}{str(consecutivo).zfill(padding)}"
