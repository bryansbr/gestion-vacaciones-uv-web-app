import logging
from datetime import date, timedelta

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db.models import Case, When, IntegerField, Q
from django.db.models.signals import post_save
from django.dispatch import receiver

from usuarios.models import Funcionario, CustomUser

from .utils import (
    calcular_plazo_limite_solicitud, 
    calcular_fecha_salida_y_pago_fuera_plazo,
    es_dia_habil,
    get_current_date_colombia,
    puede_solicitar_vacaciones_hoy,
    obtener_ultimo_dia_del_mes
)

import holidays

logger = logging.getLogger(__name__)

# ============================================================
# MODELO: PeriodoVacacional
# ============================================================
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
                return 0
        elif estamento == 'administrativo':
            return 15  # 15 días hábiles
        elif estamento == 'trabajador oficial':
            return 30  # 30 días calendario
        else:
            return 0

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
        if self.fecha_inicio_periodo and self.fecha_fin_periodo:
            return f"Del {self.fecha_inicio_periodo.strftime('%d/%m/%Y')} al {self.fecha_fin_periodo.strftime('%d/%m/%Y')}"
        
        elif self.fecha_inicio_periodo:
            return f"Desde {self.fecha_inicio_periodo.strftime('%d/%m/%Y')}"
        
        elif self.fecha_fin_periodo:
            return f"Hasta {self.fecha_fin_periodo.strftime('%d/%m/%Y')}"
        
        else:
            return "Fechas no definidas"

    class Meta:
        verbose_name = "Periodo vacacional"
        verbose_name_plural = "Periodos vacacionales"
        ordering = ['-fecha_inicio_periodo']


# ============================================================
# MODELO: SolicitudVacaciones
# ============================================================
class SolicitudVacaciones(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('en_revision', 'En revisión'),
        ('aprobado', 'Aprobada'),
        ('rechazado', 'Rechazada'),
        ('devuelta', 'Devuelta'),
        ('cancelado', 'Cancelado'),
    ]

    aprobaciones = GenericRelation(
        'AprobacionEtapa',
        related_query_name='solicitudes'
    )    
    codigo_sabs = models.CharField(max_length=50, unique=True)
    creada_por = models.ForeignKey(
        CustomUser,
        on_delete=models.PROTECT,
        related_name='solicitudes_creadas',
        verbose_name="Creada por",
        null=True, blank=True
    )
    fecha_solicitud = models.DateField(
        verbose_name="Fecha de solicitud",
        default=get_current_date_colombia
    )
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

    ETAPAS_ORDEN = ('JEFE', 'COORD', 'RRHH')

    @property
    def aprobaciones_ordenadas(self):
        orden = Case(
            When(etapa='JEFE',  then=0),
            When(etapa='COORD', then=1),
            When(etapa='RRHH',  then=2),
            output_field=IntegerField(),
        )

        return list(self.aprobaciones.order_by(orden, 'id'))

    @property
    def aprobada_por_jefe(self) -> bool:
        a = self.aprobaciones.filter(etapa='JEFE').first()
        return bool(a and a.estado == 'aprobada')

    @property
    def aprobada_por_coord(self) -> bool:
        a = self.aprobaciones.filter(etapa='COORD').first()
        return bool(a and a.estado == 'aprobada')

    @property
    def autorizada_rrhh(self) -> bool:
        a = self.aprobaciones.filter(etapa='RRHH').first()
        return bool(a and a.estado == 'autorizada')

    @property
    def etapa_activa(self):
        for a in self.aprobaciones_ordenadas:
            if a.estado == 'devuelta':
                return a
        for a in self.aprobaciones_ordenadas:
            if a.estado == 'pendiente':
                return a
                
        return None

    @staticmethod
    def color_por_estado(estado: str) -> str:
        """
        Mapea estado de etapa a color del semáforo.
        """
        estado = (estado or '').lower()
        if estado in ('aprobada', 'autorizada'):
            return 'verde'
        if estado in ('devuelta', 'rechazada'):
            return 'rojo'

        return 'amarillo'

    @property
    def estado_global(self) -> str:
        """
        Deriva un estado global legible para cabecera/tablero.
        - 'rechazada' si RRHH rechaza.
        - 'devuelta' si hay una devolución en JEFE o COORD.
        - 'autorizada' si RRHH autoriza.
        - 'en_progreso' si hay pendientes y ninguna roja.
        """
        mapa = {a.etapa: a for a in self.aprobaciones.all()}
        rrhh = mapa.get('RRHH')

        if rrhh and rrhh.estado == 'rechazada':
            return 'rechazada'
        if any(a.estado == 'devuelta' for a in self.aprobaciones.all() if a.etapa in ('JEFE', 'COORD')):
            return 'devuelta'
        if rrhh and rrhh.estado == 'autorizada':
            return 'autorizada'
        if any(a.estado == 'pendiente' for a in self.aprobaciones.all()):
            return 'en_progreso'

        return 'desconocido'

    @property
    def colores_semaforo(self):
        """
        Devuelve una lista de 3 colores en orden JEFE→COORD→RRHH.
        Reglas:
          - 'verde'  si la etapa está aprobada/autorizada
          - 'rojo'   si está devuelta/rechazada
          - 'amarillo' SOLO para la primera etapa con estado 'pendiente'
          - 'blanco' para etapas 'pendiente' que aún no son la activa (futuras)
        """
        colores = []
        activa_asignada = False
        etapas = self.aprobaciones_ordenadas

        for a in etapas:
            est = (a.estado or '').lower()
            if est in ('aprobada', 'autorizada'):
                colores.append('verde')
            elif est in ('devuelta', 'rechazada'):
                colores.append('rojo')
            elif est == 'pendiente':
                if not activa_asignada:
                    colores.append('amarillo')
                    activa_asignada = True
                else:
                    colores.append('blanco')
            else:
                colores.append('blanco')

        return colores

    @property
    def puede_editar_eliminar(self) -> bool:
        """
        Permite editar/eliminar la solicitud en los siguientes casos:
        - Estado 'pendiente': solicitud inicial o reenvío por funcionario
        - Estado 'en_revision' y hay una devolución en JEFE o COORD (no rechazada por RRHH)
        
        NO permite editar/eliminar si:
        - RRHH rechazó la solicitud (estado_global == 'rechazada')
        - RRHH autorizó la solicitud (estado_global == 'autorizada')
        """
        if self.estado_solicitud == 'pendiente':
            return True
        
        if self.estado_global == 'rechazada':
            return False
        
        if self.estado_global == 'devuelta':
            return True
        
        return False

    def _obtener_siguiente_dia_habil(self, fecha):
        festivos = holidays.Colombia(years=[fecha.year])
        siguiente_dia = fecha
        while (siguiente_dia.weekday() >= 5 or siguiente_dia in festivos):
            siguiente_dia += timedelta(days=1)

        return siguiente_dia

    def _calcular_fecha_minima_inicio_vacaciones_nuevas(self):
        hoy = get_current_date_colombia()
        estamento = self.funcionario.estamento.nombre.lower()
        decreto = (self.funcionario.decreto_resolucion or '').strip()
        plazo_resultado = calcular_plazo_limite_solicitud(estamento, decreto)
        fecha_salida_str = plazo_resultado.fecha_salida
        d, m, y = map(int, fecha_salida_str.split('/'))
        fecha_salida = date(y, m, d)
        
        if hoy <= plazo_resultado.fecha_limite:
            return fecha_salida
        else:
            fecha_salida_fuera_str, _, _ = calcular_fecha_salida_y_pago_fuera_plazo(estamento, decreto)
            d2, m2, y2 = map(int, fecha_salida_fuera_str.split('/'))
            return date(y2, m2, d2)

    def _calcular_fecha_minima_inicio_dias_pendientes(self):
        hoy = get_current_date_colombia()
        fecha_minima = hoy + timedelta(days=1)

        return self._obtener_siguiente_dia_habil(fecha_minima)

    def _calcular_fecha_minima_inicio(self):
        if self.tiene_dias_pendientes:
            return self._calcular_fecha_minima_inicio_dias_pendientes()
        else:
            return self._calcular_fecha_minima_inicio_vacaciones_nuevas()

    def _validar_fecha_inicio_es_habil(self, fecha):
        if fecha.weekday() >= 5:
            return False, "La fecha de inicio no puede ser sábado o domingo."

        festivos = holidays.Colombia(years=[fecha.year])

        if fecha in festivos:
            return False, "La fecha de inicio no puede ser un festivo."

        return True, None

    def _calcular_total_dias_solicitados(self):
        """Calcula el total de días solicitados basado en las fechas actuales."""
        if not (self.fecha_inicio_vacaciones and self.fecha_fin_vacaciones):
            return
        
        total = self._obtener_total_dias_por_estamento()

        if self.periodo_vacacional_id:
            try:
                periodo = self.periodo_vacacional
            except PeriodoVacacional.DoesNotExist:
                periodo = None

            if periodo and periodo.dias_pendientes_periodo is not None:
                try:
                    total = min(total, max(0, int(periodo.dias_pendientes_periodo)))
                except (TypeError, ValueError):
                    logger.warning(
                        "No se pudo convertir los días pendientes (%s) a entero para la solicitud %s",
                        getattr(periodo, "dias_pendientes_periodo", None),
                        self.pk,
                    )

        self.total_dias_solicitados = total

    def _obtener_total_dias_por_estamento(self):
        """
        Calcula el total de días solicitados según el estamento y decreto del funcionario.
        
        Returns:
            int: Total de días calculados según las reglas del estamento
        """
        if not (self.fecha_inicio_vacaciones and self.fecha_fin_vacaciones):
            return 0
            
        estamento = self.funcionario.estamento.nombre.lower()
        decreto = (self.funcionario.decreto_resolucion or '').strip()

        if estamento == 'docente' and decreto == '1279':
            festivos = holidays.Colombia(years=range(self.fecha_inicio_vacaciones.year, self.fecha_fin_vacaciones.year + 1))
            actual = self.fecha_inicio_vacaciones
            habiles_marcados = 0

            while actual <= self.fecha_fin_vacaciones and habiles_marcados < 15:
                if actual.weekday() < 5 and actual not in festivos:
                    habiles_marcados += 1
                actual += timedelta(days=1)

            dias_calendario = 0
            while actual <= self.fecha_fin_vacaciones and dias_calendario < 15:
                dias_calendario += 1
                actual += timedelta(days=1)

            return 15 + dias_calendario
            
        elif estamento == 'administrativo':
            festivos = holidays.Colombia(years=range(self.fecha_inicio_vacaciones.year, self.fecha_fin_vacaciones.year + 1))
            actual = self.fecha_inicio_vacaciones
            dias_habiles = 0
            while actual <= self.fecha_fin_vacaciones:
                if actual.weekday() < 5 and actual not in festivos:
                    dias_habiles += 1
                actual += timedelta(days=1)
            return dias_habiles
            
        else:
            return (self.fecha_fin_vacaciones - self.fecha_inicio_vacaciones).days + 1

    def _validar_funcionario(self, errores):
        """Valida que el funcionario pueda solicitar vacaciones."""
        if not self.funcionario.puede_solicitar_vacaciones():
            errores['funcionario'] = "El funcionario no cumple con la antigüedad mínima ni tiene días pendientes."

    def _validar_fechas(self, errores):
        """Valida las fechas de inicio y fin de vacaciones."""
        if not self.fecha_inicio_vacaciones:
            return
            
        if not self.tiene_dias_pendientes:
            puede_solicitar, mensaje_plazo = puede_solicitar_vacaciones_hoy(
                self.funcionario.estamento.nombre.lower(),
                self.funcionario.decreto_resolucion
            )
            if not puede_solicitar:
                errores['fecha_inicio_vacaciones'] = mensaje_plazo
            else:
                if not es_dia_habil(self.fecha_inicio_vacaciones):
                    errores['fecha_inicio_vacaciones'] = "La fecha de inicio debe ser un día hábil (no puede ser fin de semana ni festivo)."
                else:
                    fecha_minima = self._calcular_fecha_minima_inicio()
                    if self.fecha_inicio_vacaciones < fecha_minima:
                        errores['fecha_inicio_vacaciones'] = (
                            f"La fecha de inicio debe ser al menos {fecha_minima.strftime('%d/%m/%Y')}. "
                            f"{mensaje_plazo}"
                        )

        if self.tiene_dias_pendientes:
            if not es_dia_habil(self.fecha_inicio_vacaciones):
                errores['fecha_inicio_vacaciones'] = "La fecha de inicio debe ser un día hábil (no puede ser fin de semana ni festivo)."
            else:
                fecha_minima = self._calcular_fecha_minima_inicio()
                if self.fecha_inicio_vacaciones < fecha_minima:
                    errores['fecha_inicio_vacaciones'] = (
                        f"Para vacaciones por días pendientes, la fecha de inicio debe ser al menos "
                        f"un día después de la fecha de solicitud. "
                        f"La fecha mínima permitida es {fecha_minima.strftime('%d/%m/%Y')}."
                    )

    def _validar_cruces(self, errores):
        """Valida que no haya cruces con otras solicitudes."""
        if not (self.fecha_inicio_vacaciones and self.fecha_fin_vacaciones):
            return
            
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

    def _validar_dias_solicitados(self, errores):
        """Valida el cálculo de días solicitados según estamento y decreto."""
        if not (self.fecha_inicio_vacaciones and self.fecha_fin_vacaciones):
            return
            
        estamento = self.funcionario.estamento.nombre.lower()
        decreto = (self.funcionario.decreto_resolucion or '').strip()
        dias_solicitados = (self.fecha_fin_vacaciones - self.fecha_inicio_vacaciones).days + 1
        
        if estamento == 'docente' and decreto == '1279':
            festivos = holidays.Colombia(years=range(self.fecha_inicio_vacaciones.year, self.fecha_fin_vacaciones.year + 1))
            actual = self.fecha_inicio_vacaciones
            habiles_marcados = 0
            while actual <= self.fecha_fin_vacaciones and habiles_marcados < 15:
                if actual.weekday() < 5 and actual not in festivos:
                    habiles_marcados += 1
                actual += timedelta(days=1)

            dias_calendario = 0
            while actual <= self.fecha_fin_vacaciones and dias_calendario < 15:
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
                actual = self.fecha_inicio_vacaciones
                dias_habiles = 0
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

    def _validar_periodo_vacacional(self, errores):
        """Valida que haya suficientes días disponibles en el periodo vacacional."""
        if self.periodo_vacacional and self.total_dias_solicitados is not None and self.periodo_vacacional.dias_pendientes_periodo is not None:
            if self.total_dias_solicitados > self.periodo_vacacional.dias_pendientes_periodo:
                errores['periodo_vacacional'] = "No hay suficientes días pendientes disponibles en el periodo seleccionado."
        elif self.total_dias_solicitados is None:
            errores['total_dias_solicitados'] = "Debe ingresar el número de días solicitados."

    def clean(self):
        """Valida la solicitud de vacaciones."""
        errores = {}
        
        self._calcular_total_dias_solicitados()
        
        self._validar_funcionario(errores)
        self._validar_fechas(errores)
        self._validar_cruces(errores)
        self._validar_dias_solicitados(errores)
        self._validar_periodo_vacacional(errores)

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
            self.total_dias_solicitados = self._obtener_total_dias_por_estamento()

        if not self.codigo_sabs:
            anio_codigo = self.fecha_solicitud.year if self.fecha_solicitud else get_current_date_colombia().year
            self.codigo_sabs = generar_codigo_sabs('VAC', anio_codigo)
            
        if not self.fecha_pago:
            self.fecha_pago = self._calcular_fecha_pago_automatica()
        
        super().save(*args, **kwargs)

    def _calcular_fecha_pago_automatica(self):
        hoy = get_current_date_colombia()
        estamento = self.funcionario.estamento.nombre.lower()
        decreto = (self.funcionario.decreto_resolucion or '').strip()
        plazo_resultado = calcular_plazo_limite_solicitud(estamento, decreto)
        if hoy <= plazo_resultado.fecha_limite:
            if estamento == 'docente' or estamento == 'trabajador oficial':
                fecha_pago = obtener_ultimo_dia_del_mes(hoy.year, hoy.month)
            else:
                fecha_pago = date(hoy.year, hoy.month, 15)
        else:
            _, fecha_pago_fuera_str, _ = calcular_fecha_salida_y_pago_fuera_plazo(estamento, decreto)
            d, m, y = map(int, fecha_pago_fuera_str.split('/'))
            fecha_pago = date(y, m, d)
        return fecha_pago


# ============================================================
# MODELO: AprobacionEtapa (Semáforo)
# ============================================================
class AprobacionEtapa(models.Model):
    ETAPA = [
        ('JEFE', 'Jefe Inmediato'),
        ('COORD', 'Coordinación Administrativa'),
        ('RRHH', 'División de Recursos Humanos'),
    ]
    ESTADO = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('devuelta', 'Devuelta'),
        ('rechazada', 'Rechazada'),
        ('autorizada', 'Autorizada'),
    ]

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    solicitud = models.ForeignKey(
        SolicitudVacaciones,
        on_delete=models.CASCADE,
        related_name='aprobaciones',
        null=True,
        blank=True,
    )
    etapa = models.CharField(max_length=5, choices=ETAPA)
    estado = models.CharField(max_length=10, choices=ESTADO, default='pendiente')
    observacion = models.TextField(blank=True, null=True)
    actualizado_por = models.ForeignKey('usuarios.CustomUser', null=True, blank=True, on_delete=models.SET_NULL)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Aprobación por etapa"
        verbose_name_plural = "Aprobaciones por etapa"
        constraints = [
            models.UniqueConstraint(
                fields=['content_type', 'object_id', 'etapa'],
                name='uniq_aprobacion_content_object_etapa',
            ),
        ]
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]

    def save(self, *args, **kwargs):
        if self.content_type_id is None and self.object_id is None:
            if self.solicitud_id:
                ct = ContentType.objects.get_for_model(SolicitudVacaciones)
                self.content_type = ct
                self.object_id = self.solicitud_id
        super().save(*args, **kwargs)

    def __str__(self):
        target = self.content_object
        target_label = getattr(target, 'codigo_sabs', str(target.pk))
        return f"{self.get_etapa_display()} – {self.get_estado_display()} – {target_label}"


# ============================================================
# Crear etapas por defecto al crear una Solicitud
# ============================================================
@receiver(post_save, sender=SolicitudVacaciones)
def crear_etapas_por_defecto(sender, instance: SolicitudVacaciones, created, **kwargs):
    """
    Crea las 3 etapas en 'pendiente' al crear la solicitud.
    """
    if not created:
        return

    existentes = set(instance.aprobaciones.values_list('etapa', flat=True))
    por_crear = [e for e in SolicitudVacaciones.ETAPAS_ORDEN if e not in existentes]

    if not por_crear:
        return

    ct_sol = ContentType.objects.get_for_model(SolicitudVacaciones)
    objs = [
        AprobacionEtapa(
            solicitud=instance,
            etapa=e,
            estado='pendiente',
            content_type=ct_sol,
            object_id=instance.pk,
        )
        for e in por_crear
    ]
    AprobacionEtapa.objects.bulk_create(objs)


# ============================================================
# MODELO: DiasPendientesVacaciones
# ============================================================
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


# ============================================================
# MODELO: ReintegroVacaciones
# ============================================================
class ReintegroVacaciones(models.Model):
    TIPO_DIAS = (
        ('H', 'Hábiles'),
        ('C', 'Calendario'),
        ('HC', 'Hábiles y Calendario'),
        ('N/A', 'No aplica'),
    )
    MOTIVOS_REINTEGRO = [
        ('finalizacion_normal', 'Finalización normal del periodo'),
        ('suspension_anticipada', 'Suspensión anticipada por necesidad del servicio'),
    ]
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('en_revision', 'En revisión'),
        ('devuelta', 'Devuelta'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('cancelado', 'Cancelado'),
        ('completado', 'Completado'),
    ]

    aprobaciones = GenericRelation(
        'AprobacionEtapa',
        related_query_name='reintegros'
    )
    codigo_sabs = models.CharField(max_length=50, unique=True)
    creada_por = models.ForeignKey(
        CustomUser,
        on_delete=models.PROTECT,
        related_name='reintegros_creados',
        verbose_name="Creado por",
        null=True, blank=True
    )
    fecha_solicitud = models.DateField(auto_now_add=True)
    fecha_reintegro = models.DateField()
    motivo_reintegro = models.CharField(max_length=50, choices=MOTIVOS_REINTEGRO)
    observaciones = models.TextField(blank=True, null=True)
    periodo_correspondiente_desde = models.DateField(null=True, blank=True)
    periodo_correspondiente_hasta = models.DateField(null=True, blank=True)
    fecha_disfrute_desde = models.DateField()
    fecha_disfrute_hasta = models.DateField()
    dias_disfrutados = models.IntegerField(default=0)
    tipo_dias_disfrutados = models.CharField(max_length=3, choices=TIPO_DIAS, default='N/A')
    dias_pendientes = models.IntegerField(default=0)
    tipo_dias_pendientes = models.CharField(max_length=3, choices=TIPO_DIAS, default='N/A')
    dias_disfrutados_habiles = models.IntegerField(default=0)
    dias_disfrutados_calendario = models.IntegerField(default=0)
    dias_pendientes_habiles = models.IntegerField(default=0)
    dias_pendientes_calendario = models.IntegerField(default=0)
    es_reintegro_anticipado = models.BooleanField(default=False)
    firmado_por = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        related_name='reintegros_firmados',
        null=True,
        blank=True
    )
    firmado_en = models.DateTimeField(null=True, blank=True)
    periodo_vacacional = models.ForeignKey(PeriodoVacacional, on_delete=models.PROTECT)
    solicitud_vacaciones = models.ForeignKey(SolicitudVacaciones, on_delete=models.PROTECT)
    funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.PROTECT,
        related_name="reintegros_vacaciones"
    )
    estado_solicitud = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')

    ETAPAS_ORDEN = ('JEFE', 'COORD', 'RRHH')

    @property
    def aprobaciones_ordenadas(self):
        orden = Case(
            When(etapa='JEFE', then=0),
            When(etapa='COORD', then=1),
            When(etapa='RRHH', then=2),
            output_field=IntegerField(),
        )
        return list(self.aprobaciones.order_by(orden, 'id'))

    @property
    def etapa_activa(self):
        for a in self.aprobaciones_ordenadas:
            if a.estado == 'devuelta':
                return a
        for a in self.aprobaciones_ordenadas:
            if a.estado == 'pendiente':
                return a
        return None

    @property
    def aprobada_por_jefe(self) -> bool:
        a = self.aprobaciones.filter(etapa='JEFE').first()
        return bool(a and a.estado == 'aprobada')

    @property
    def aprobada_por_coord(self) -> bool:
        a = self.aprobaciones.filter(etapa='COORD').first()
        return bool(a and a.estado == 'aprobada')

    @property
    def autorizada_rrhh(self) -> bool:
        a = self.aprobaciones.filter(etapa='RRHH').first()
        return bool(a and a.estado == 'autorizada')

    @property
    def estado_global(self) -> str:
        mapa = {a.etapa: a for a in self.aprobaciones.all()}
        rrhh = mapa.get('RRHH')

        if rrhh and rrhh.estado == 'rechazada':
            return 'rechazada'
        if any(a.estado == 'devuelta' for a in self.aprobaciones.all() if a.etapa in ('JEFE', 'COORD')):
            return 'devuelta'
        if rrhh and rrhh.estado == 'autorizada':
            return 'autorizada'
        if any(a.estado == 'pendiente' for a in self.aprobaciones.all()):
            return 'en_progreso'
        return 'desconocido'

    @property
    def colores_semaforo(self):
        colores = []
        activa_asignada = False
        etapas = self.aprobaciones_ordenadas

        for a in etapas:
            est = (a.estado or '').lower()
            if est in ('aprobada', 'autorizada'):
                colores.append('verde')
            elif est in ('devuelta', 'rechazada'):
                colores.append('rojo')
            elif est == 'pendiente':
                if not activa_asignada:
                    colores.append('amarillo')
                    activa_asignada = True
                else:
                    colores.append('blanco')
            else:
                colores.append('blanco')
        return colores

    @property
    def puede_editar_eliminar(self) -> bool:
        if self.estado_solicitud == 'pendiente':
            return True
        if self.estado_global == 'rechazada':
            return False
        if self.estado_global == 'devuelta':
            return True
        return False

    @property
    def dias_disfrutados_total(self) -> int:
        return max(0, (self.dias_disfrutados_habiles or 0) + (self.dias_disfrutados_calendario or 0))

    @property
    def dias_pendientes_total(self) -> int:
        return max(0, (self.dias_pendientes_habiles or 0) + (self.dias_pendientes_calendario or 0))

    def _actualizar_resumen_dias(self):
        self.dias_disfrutados = self.dias_disfrutados_total
        self.dias_pendientes = self.dias_pendientes_total

        tipo_disfrutados = 'N/A'
        if self.dias_disfrutados_habiles and self.dias_disfrutados_calendario:
            tipo_disfrutados = 'HC'
        elif self.dias_disfrutados_habiles:
            tipo_disfrutados = 'H'
        elif self.dias_disfrutados_calendario:
            tipo_disfrutados = 'C'
        self.tipo_dias_disfrutados = tipo_disfrutados

        tipo_pendientes = 'N/A'
        if self.dias_pendientes_habiles and self.dias_pendientes_calendario:
            tipo_pendientes = 'HC'
        elif self.dias_pendientes_habiles:
            tipo_pendientes = 'H'
        elif self.dias_pendientes_calendario:
            tipo_pendientes = 'C'
        self.tipo_dias_pendientes = tipo_pendientes

    def clean(self):
        if self.fecha_disfrute_desde and self.fecha_disfrute_hasta:
            if self.fecha_disfrute_desde > self.fecha_disfrute_hasta:
                raise ValidationError("La fecha de inicio del disfrute no puede ser posterior a la fecha final.")
        if self.fecha_reintegro and self.fecha_disfrute_hasta and self.fecha_reintegro <= self.fecha_disfrute_hasta:
            raise ValidationError("La fecha de reintegro debe ser posterior al último día del disfrute.")

        if self.es_reintegro_anticipado and not (self.observaciones and self.observaciones.strip()):
            raise ValidationError("Las observaciones son obligatorias cuando el reintegro es anticipado.")

        if self.solicitud_vacaciones_id:
            otras = ReintegroVacaciones.objects.filter(
                solicitud_vacaciones_id=self.solicitud_vacaciones_id
            ).exclude(pk=self.pk)
            otras = otras.exclude(estado_solicitud__in=['rechazado', 'cancelado', 'completado'])
            if otras.exists():
                raise ValidationError("Ya existe un reintegro activo asociado a la solicitud seleccionada.")

            if not self.solicitud_vacaciones.autorizada_rrhh:
                raise ValidationError("Solo se pueden crear reintegros de solicitudes autorizadas por RRHH.")

        self._actualizar_resumen_dias()

    def save(self, *args, **kwargs):
        if not self.codigo_sabs:
            anio_codigo = self.fecha_solicitud.year if self.fecha_solicitud else get_current_date_colombia().year
            self.codigo_sabs = generar_codigo_sabs('REI', anio_codigo)
        self.full_clean()
        super().save(*args, **kwargs)

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
        constraints = [
            models.UniqueConstraint(
                fields=['solicitud_vacaciones'],
                condition=Q(estado_solicitud__in=['pendiente', 'en_revision', 'devuelta', 'aprobado']),
                name='uniq_reintegro_activo_por_solicitud'
            )
        ]


@receiver(post_save, sender=ReintegroVacaciones)
def crear_etapas_por_defecto_reintegro(sender, instance: ReintegroVacaciones, created, **kwargs):
    if not created:
        return

    existentes = set(instance.aprobaciones.values_list('etapa', flat=True))
    por_crear = [e for e in ReintegroVacaciones.ETAPAS_ORDEN if e not in existentes]

    if not por_crear:
        return

    ct_reintegro = ContentType.objects.get_for_model(ReintegroVacaciones)
    objs = [
        AprobacionEtapa(
            content_type=ct_reintegro,
            object_id=instance.pk,
            etapa=e,
            estado='pendiente',
        )
        for e in por_crear
    ]
    AprobacionEtapa.objects.bulk_create(objs)


# ============================================================
# MODELO: HistoricoAcciones
# ============================================================
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


# ============================================================
# Utilidad: Generador de código SABS
# ============================================================
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
    
    ultimo_codigo = modelo.objects.filter(
        codigo_sabs__startswith=f"{tipo}{anio}"
    ).order_by('-codigo_sabs').first()
    
    if ultimo_codigo:
        try:
            codigo_completo = ultimo_codigo.codigo_sabs
            numero_str = codigo_completo[len(f"{tipo}{anio}"):]
            consecutivo = int(numero_str) + 1 if numero_str.isdigit() else 1
        except ValueError:
            consecutivo = 1
    else:
        consecutivo = 1
    
    return f"{tipo}{anio}{str(consecutivo).zfill(4)}"
