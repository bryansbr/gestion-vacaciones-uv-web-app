from datetime import date, datetime, timedelta
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
        """
        Calcula los días de vacaciones que otorga este periodo según el estamento del funcionario.
        NO calcula días entre fechas, sino los días de vacaciones a los que tiene derecho.
        """
        estamento = self.funcionario.estamento.nombre.lower()
        decreto = (self.funcionario.decreto_resolucion or '').strip()

        if estamento == 'docente':
            if decreto == '1279':
                return 30  # 15 días hábiles + 15 días calendario
            elif decreto == '115':
                return 30  # 30 días calendario
            else:
                return 0   # Sin decreto válido
        elif estamento == 'administrativo':
            return 15  # 15 días hábiles
        elif estamento == 'trabajador oficial':
            return 30  # 30 días calendario
        else:
            return 0   # Estamento no reconocido

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
        return f"Del {self.fecha_inicio_periodo.strftime('%d-%m-%Y')} al {self.fecha_fin_periodo.strftime('%d-%m-%Y')}"

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
    fecha_solicitud = models.DateField(verbose_name="Fecha de solicitud")
    fecha_inicio_vacaciones = models.DateField()
    fecha_fin_vacaciones = models.DateField()
    total_dias_solicitados = models.IntegerField()
    fecha_pago = models.DateField(
        verbose_name="Fecha de pago", 
        help_text="Fecha calculada automáticamente según el calendario de pagos",
        null=True,
        blank=True
    )
    observaciones = models.TextField(blank=True, null=True)
    tiene_dias_pendientes = models.BooleanField(default=False)

    periodo_vacacional = models.ForeignKey(PeriodoVacacional, on_delete=models.PROTECT)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE)
    estado_solicitud = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')

    def _obtener_siguiente_dia_habil(self, fecha):
        """Retorna el siguiente día hábil a partir de una fecha dada."""
        festivos = holidays.Colombia(years=[fecha.year])
        siguiente_dia = fecha
        
        while (siguiente_dia.weekday() >= 5 or siguiente_dia in festivos):
            siguiente_dia += timedelta(days=1)
        
        return siguiente_dia

    def _calcular_fecha_minima_inicio_vacaciones_nuevas(self):
        """
        Calcula la fecha mínima permitida para iniciar vacaciones nuevas
        según el calendario de pagos y plazos administrativos.
        """
        
        hoy = date.today()
        estamento = self.funcionario.estamento.nombre.lower()
        decreto = (self.funcionario.decreto_resolucion or '').strip()
        
        # Calcular fechas de pago según estamento
        if estamento == 'docente':
            # Docentes: pago el día 30 de cada mes
            # Plazo máximo: día 10 del mes para salir el 1º del mes siguiente
            if hoy.day <= 10:
                # Si estamos antes del día 10, puede salir el 1º del mes siguiente
                fecha_salida = date(hoy.year, hoy.month + 1, 1) if hoy.month < 12 else date(hoy.year + 1, 1, 1)
            else:
                # Si estamos después del día 10, debe esperar hasta el 1º del mes siguiente al próximo
                if hoy.month == 12:
                    fecha_salida = date(hoy.year + 1, 2, 1)
                elif hoy.month == 11:
                    fecha_salida = date(hoy.year + 1, 1, 1)
                else:
                    fecha_salida = date(hoy.year, hoy.month + 2, 1)
        else:
            # Administrativos y trabajadores oficiales: pago quincenal (15 y 30)
            # Plazo máximo: día 3 para salir el 16, día 17 para salir el 1º del mes siguiente
            if hoy.day <= 3:
                # Puede salir el 16 del mes actual
                fecha_salida = date(hoy.year, hoy.month, 16)
            elif hoy.day <= 17:
                # Puede salir el 1º del mes siguiente
                fecha_salida = date(hoy.year, hoy.month + 1, 1) if hoy.month < 12 else date(hoy.year + 1, 1, 1)
            else:
                # Debe esperar hasta el 16 del mes siguiente
                if hoy.month == 12:
                    fecha_salida = date(hoy.year + 1, 1, 16)
                else:
                    fecha_salida = date(hoy.year, hoy.month + 1, 16)
        
        # Asegurar que la fecha de salida sea un día hábil
        return self._obtener_siguiente_dia_habil(fecha_salida)

    def _calcular_fecha_minima_inicio_dias_pendientes(self):
        """
        Calcula la fecha mínima permitida para iniciar vacaciones por días pendientes.
        Permite solicitar con un día de anticipación.
        """
        
        hoy = date.today()
        # Para días pendientes, permite solicitar con un día de anticipación
        fecha_minima = hoy + timedelta(days=1)
        
        return self._obtener_siguiente_dia_habil(fecha_minima)

    def _calcular_fecha_minima_inicio(self):
        """
        Calcula la fecha mínima permitida para iniciar vacaciones
        según si son vacaciones nuevas o por días pendientes.
        """
        if self.tiene_dias_pendientes:
            return self._calcular_fecha_minima_inicio_dias_pendientes()
        else:
            return self._calcular_fecha_minima_inicio_vacaciones_nuevas()

    def _validar_fecha_inicio_es_habil(self, fecha):
        """
        Valida que la fecha de inicio no sea sábado, domingo o festivo.
        """
        if fecha.weekday() >= 5:
            return False, "La fecha de inicio no puede ser sábado o domingo."
        
        festivos = holidays.Colombia(years=[fecha.year])
        if fecha in festivos:
            return False, "La fecha de inicio no puede ser un festivo."
        
        return True, None

    def clean(self):
        errores = {}
        # Calcular total_dias_solicitados si no está establecido
        if self.fecha_inicio_vacaciones and self.fecha_fin_vacaciones and self.total_dias_solicitados is None:
            estamento = self.funcionario.estamento.nombre.lower()
            decreto = (self.funcionario.decreto_resolucion or '').strip()

            if estamento == 'docente' and decreto == '1279':
                festivos = holidays.Colombia(years=range(self.fecha_inicio_vacaciones.year, self.fecha_fin_vacaciones.year + 1))
                dias_habiles = 0
                actual = self.fecha_inicio_vacaciones
                habiles_marcados = 0
                
                while actual <= self.fecha_fin_vacaciones and habiles_marcados < 15:
                    if actual.weekday() < 5 and actual not in festivos:
                        habiles_marcados += 1
                    actual += timedelta(days=1)
                dias_calendario = 0

                while actual <= self.fecha_fin_vacaciones:
                    dias_calendario += 1
                    actual += timedelta(days=1)
                self.total_dias_solicitados = 15 + dias_calendario
            elif estamento == 'administrativo':
                festivos = holidays.Colombia(years=range(self.fecha_inicio_vacaciones.year, self.fecha_fin_vacaciones.year + 1))
                dias_habiles = 0
                actual = self.fecha_inicio_vacaciones
                
                while actual <= self.fecha_fin_vacaciones:
                    if actual.weekday() < 5 and actual not in festivos:
                        dias_habiles += 1
                    actual += timedelta(days=1)
                self.total_dias_solicitados = dias_habiles
            else:
                self.total_dias_solicitados = (self.fecha_fin_vacaciones - self.fecha_inicio_vacaciones).days + 1
            
        if not self.funcionario.puede_solicitar_vacaciones():
            errores['funcionario'] = "El funcionario no cumple con la antigüedad mínima ni tiene días pendientes."

        if self.fecha_inicio_vacaciones:
            es_habil, mensaje_error = self._validar_fecha_inicio_es_habil(self.fecha_inicio_vacaciones)
            
            if not es_habil:
                errores['fecha_inicio_vacaciones'] = mensaje_error
            else:
                fecha_minima = self._calcular_fecha_minima_inicio()
                if self.fecha_inicio_vacaciones < fecha_minima:
                    if self.tiene_dias_pendientes:
                        errores['fecha_inicio_vacaciones'] = (
                            f"Para vacaciones por días pendientes, la fecha de inicio debe ser al menos "
                            f"un día después de la fecha de solicitud. "
                            f"La fecha mínima permitida es {fecha_minima.strftime('%d/%m/%Y')}."
                        )
                    else:
                        estamento = self.funcionario.estamento.nombre.lower()
                        if estamento == 'docente':
                            errores['fecha_inicio_vacaciones'] = (
                                f"Para docentes, las solicitudes deben presentarse máximo hasta el día 10 del mes "
                                f"para salir a vacaciones el 1º del mes siguiente. "
                                f"La fecha mínima permitida es {fecha_minima.strftime('%d/%m/%Y')}."
                            )
                        else:
                            errores['fecha_inicio_vacaciones'] = (
                                f"Para administrativos y trabajadores oficiales, las solicitudes deben presentarse "
                                f"máximo hasta el día 3 del mes para salir el 16, o hasta el día 17 para salir "
                                f"el 1º del mes siguiente. La fecha mínima permitida es {fecha_minima.strftime('%d/%m/%Y')}."
                            )

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

        # Validación de cálculo de días según estamento y decreto
        if self.fecha_inicio_vacaciones and self.fecha_fin_vacaciones:
            estamento = self.funcionario.estamento.nombre.lower()
            decreto = (self.funcionario.decreto_resolucion or '').strip()
            dias_solicitados = (self.fecha_fin_vacaciones - self.fecha_inicio_vacaciones).days + 1
            
            if estamento == 'docente' and decreto == '1279':
                festivos = holidays.Colombia(years=range(self.fecha_inicio_vacaciones.year, self.fecha_fin_vacaciones.year + 1))
                dias_habiles = 0
                actual = self.fecha_inicio_vacaciones
                habiles_marcados = 0
                
                while actual <= self.fecha_fin_vacaciones and habiles_marcados < 15:
                    if actual.weekday() < 5 and actual not in festivos:
                        habiles_marcados += 1
                    actual += timedelta(days=1)
                dias_calendario = 0
                
                while actual <= self.fecha_fin_vacaciones:
                    dias_calendario += 1
                    actual += timedelta(days=1)
                total = 15 + dias_calendario
                if total != self.total_dias_solicitados:
                    errores[None] = (
                        f"Se calcularon {total} días (15 hábiles y {dias_calendario} calendario), pero se intentó guardar {self.total_dias_solicitados}."
                    )
            elif estamento == 'administrativo' or (estamento == 'docente' and decreto == '115'):
                if estamento == 'administrativo':
                    festivos = holidays.Colombia(years=range(self.fecha_inicio_vacaciones.year, self.fecha_fin_vacaciones.year + 1))
                    dias_habiles = 0
                    actual = self.fecha_inicio_vacaciones
                    
                    while actual <= self.fecha_fin_vacaciones:
                        if actual.weekday() < 5 and actual not in festivos:
                            dias_habiles += 1
                        actual += timedelta(days=1)
                    if dias_habiles != self.total_dias_solicitados:
                        errores[None] = (
                            f"Se calcularon {dias_habiles} días hábiles, pero se intentó guardar {self.total_dias_solicitados}."
                        )
                else:
                    if dias_solicitados != self.total_dias_solicitados:
                        errores[None] = (
                            f"Se calcularon {dias_solicitados} días calendario, pero se intentó guardar {self.total_dias_solicitados}."
                        )
            elif estamento == 'trabajador oficial':
                if dias_solicitados != self.total_dias_solicitados:
                    errores[None] = (
                        f"Se calcularon {dias_solicitados} días calendario, pero se intentó guardar {self.total_dias_solicitados}."
                    )
            else:
                if dias_solicitados != self.total_dias_solicitados:
                    errores[None] = (
                        f"Se calcularon {dias_solicitados} días calendario, pero se intentó guardar {self.total_dias_solicitados}."
                    )

        # Validación de días disponibles en el periodo vacacional
        if self.periodo_vacacional and self.total_dias_solicitados is not None and self.periodo_vacacional.dias_pendientes_periodo is not None:
            if self.total_dias_solicitados > self.periodo_vacacional.dias_pendientes_periodo:
                errores['periodo_vacacional'] = "No hay suficientes días pendientes disponibles en el periodo seleccionado."
        elif self.total_dias_solicitados is None:
            errores['total_dias_solicitados'] = "Debe ingresar el número de días solicitados."

        if errores:
            if None in errores:
                raise ValidationError(list(errores.values()))
            else:
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
        # Calcular automáticamente el total de días solicitados antes de guardar
        if self.fecha_inicio_vacaciones and self.fecha_fin_vacaciones:
            estamento = self.funcionario.estamento.nombre.lower()
            decreto = (self.funcionario.decreto_resolucion or '').strip()

            if estamento == 'docente' and decreto == '1279':
                festivos = holidays.Colombia(years=range(self.fecha_inicio_vacaciones.year, self.fecha_fin_vacaciones.year + 1))
                dias_habiles = 0
                actual = self.fecha_inicio_vacaciones
                habiles_marcados = 0
                
                while actual <= self.fecha_fin_vacaciones and habiles_marcados < 15:
                    if actual.weekday() < 5 and actual not in festivos:
                        habiles_marcados += 1
                    actual += timedelta(days=1)
                dias_calendario = 0

                while actual <= self.fecha_fin_vacaciones:
                    dias_calendario += 1
                    actual += timedelta(days=1)
                self.total_dias_solicitados = 15 + dias_calendario
            elif estamento == 'administrativo':
                festivos = holidays.Colombia(years=range(self.fecha_inicio_vacaciones.year, self.fecha_fin_vacaciones.year + 1))
                dias_habiles = 0
                actual = self.fecha_inicio_vacaciones
                
                while actual <= self.fecha_fin_vacaciones:
                    if actual.weekday() < 5 and actual not in festivos:
                        dias_habiles += 1
                    actual += timedelta(days=1)
                self.total_dias_solicitados = dias_habiles
            else:
                self.total_dias_solicitados = (self.fecha_fin_vacaciones - self.fecha_inicio_vacaciones).days + 1
        if not self.codigo_sabs:
            # Usar el año de la fecha de solicitud para generar el código
            anio_codigo = self.fecha_solicitud.year if self.fecha_solicitud else datetime.now().year
            self.codigo_sabs = generar_codigo_sabs('VAC', anio_codigo)
            
        # Calcular automáticamente la fecha de pago si no está establecida
        if not self.fecha_pago:
            self.fecha_pago = self._calcular_fecha_pago_automatica()
        
        super().save(*args, **kwargs)

    def _calcular_fecha_pago_automatica(self):
        """
        Calcula automáticamente la fecha de pago según el tipo de funcionario
        y la fecha de solicitud, siguiendo las reglas establecidas.
        """
        hoy = date.today()
        estamento = self.funcionario.estamento.nombre.lower()
        decreto = (self.funcionario.decreto_resolucion or '').strip()
        
        if estamento == 'docente':
            # Docentes: pago mensual el día 30
            # Si la solicitud se hace antes del día 10, el pago es el 30 del mes actual
            # Si se hace después del día 10, el pago es el 30 del mes siguiente
            if hoy.day <= 10:
                if hoy.month == 12:
                    fecha_pago = date(hoy.year, 12, 30)
                else:
                    fecha_pago = date(hoy.year, hoy.month, 30)
            else:
                # Pago el 30 del mes siguiente
                if hoy.month == 12:
                    fecha_pago = date(hoy.year + 1, 1, 30)
                else:
                    fecha_pago = date(hoy.year, hoy.month + 1, 30)
        else:
            # Administrativos y trabajadores oficiales: pago quincenal (15 y 30)
            if hoy.day <= 3:
                # Pago el 15 del mes actual
                fecha_pago = date(hoy.year, hoy.month, 15)
            elif hoy.day <= 18:
                # Pago el 30 del mes actual
                fecha_pago = date(hoy.year, hoy.month, 30)
            else:
                # Pago el 15 del mes siguiente
                if hoy.month == 12:
                    fecha_pago = date(hoy.year + 1, 1, 15)
                else:
                    fecha_pago = date(hoy.year, hoy.month + 1, 15)
        
        return fecha_pago

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
    fecha_solicitud = models.DateField(auto_now_add=True)
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
            # Usar el año de la fecha de solicitud para generar el código
            anio_codigo = self.fecha_solicitud.year if self.fecha_solicitud else datetime.now().year
            self.codigo_sabs = generar_codigo_sabs('REI', anio_codigo)
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
    
    # Buscar el último código del año actual
    ultimo_codigo = modelo.objects.filter(
        codigo_sabs__startswith=f"{tipo}{anio}"
    ).order_by('-codigo_sabs').first()
    
    if ultimo_codigo:
        try:
            # Extraer el número consecutivo del código
            codigo_completo = ultimo_codigo.codigo_sabs
            # El formato es VAC20250001, REI20250001, etc.
            # Extraer solo los números después del año
            numero_str = codigo_completo[len(f"{tipo}{anio}"):]
            if numero_str.isdigit():
                consecutivo = int(numero_str) + 1
            else:
                consecutivo = 1
        except (ValueError, IndexError, AttributeError):
            consecutivo = 1
    else:
        consecutivo = 1
    
    # Formatear con 4 dígitos
    return f"{tipo}{anio}{str(consecutivo).zfill(4)}"
