import holidays
import json

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView

from core.permissions import group_required
from usuarios.models import Funcionario
from .forms import SolicitudVacacionesForm, ReintegroVacacionesForm
from .models import (
    PeriodoVacacional,
    ReintegroVacaciones,
    SolicitudVacaciones,
    generar_codigo_sabs
)
from .services.aprobaciones import (
    aprobar_etapa,
    devolver_etapa,
    enviar_al_proximo_revisor,
)
from .services.reintegros import (
    aprobar_etapa_reintegro,
    devolver_etapa_reintegro,
)

from .utils import get_current_date_colombia
from .views import ReintegroVacacionesListView

# ==========================================================
# CONSTANTES
# ==========================================================
JEFE_SOLICITUDES_TEMPLATE = "vacaciones/roles/jefe/jefe-solicitudes-list.html"
JEFE_SOLICITUDES_TABLE_PARTIAL = "vacaciones/partials/_tabla-solicitudes.html"
JEFE_SOLICITUD_FORM_TEMPLATE = "vacaciones/roles/jefe/jefe-solicitud-form.html"
JEFE_REINTEGROS_TEMPLATE = "vacaciones/roles/jefe/jefe-reintegros-list.html"
JEFE_REINTEGROS_TABLE_PARTIAL = "vacaciones/partials/_tabla-jefe-reintegros.html"
JEFE_REINTEGRO_FORM_TEMPLATE = "vacaciones/roles/jefe/jefe-reintegro-form.html"

def _es_jefe_de(solicitud, user):
    user_func = getattr(user, "funcionario", None)
    if not user_func:
        return False
    return solicitud.funcionario.jefe_inmediato_id == user_func.pk

def _es_jefe_de_reintegro(reintegro, user):
    user_func = getattr(user, "funcionario", None)
    if not user_func:
        return False
    return reintegro.funcionario.jefe_inmediato_id == user_func.pk

@method_decorator(group_required("Jefe Inmediato", "Coordinador Administrativo"), name="dispatch")
class SolicitudesJefeListView(LoginRequiredMixin, ListView):
    """
    Lista las solicitudes de vacaciones que el jefe puede ver:
    - De funcionarios que tienen el mismo jefe_inmediato que él
    - Incluye todas las solicitudes de los subordinados
    """
    model = SolicitudVacaciones
    template_name = JEFE_SOLICITUDES_TEMPLATE
    context_object_name = "solicitudes"

    def get(self, request, *args, **kwargs):
        if request.htmx:
            self.object_list = self.get_queryset()
            context = self.get_context_data()
            context['tabla_id'] = 'tabla-solicitudes-jefe'
            html = render_to_string(JEFE_SOLICITUDES_TABLE_PARTIAL, context, request)
            return HttpResponse(html)
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        jefe_func = getattr(self.request.user, "funcionario", None)

        if not jefe_func:
            return SolicitudVacaciones.objects.none()

        qs = (SolicitudVacaciones.objects
              .select_related("funcionario", "periodo_vacacional", "creada_por", "creada_por__funcionario")
              .filter(funcionario__jefe_inmediato=jefe_func)
              .order_by("-fecha_solicitud", "-id"))


        return qs

    def _verificar_periodos_con_dias_disponibles(self, funcionario):
        """
        Verifica si el funcionario tiene periodos vacacionales con días disponibles.
        Retorna True si hay al menos un periodo con días pendientes > 0.
        """
        periodos = PeriodoVacacional.objects.filter(funcionario=funcionario)
        if not periodos.exists():
            return False
        
        periodo_ids = [p.pk for p in periodos]

        solicitudes_aprobadas = SolicitudVacaciones.objects.filter(
            periodo_vacacional_id__in=periodo_ids,
            estado_solicitud__in=['aprobado', 'autorizada']
        ).select_related('funcionario', 'funcionario__estamento')
        
        solicitudes_por_periodo = {}
        for solicitud in solicitudes_aprobadas:
            periodo_id = solicitud.periodo_vacacional_id
            if periodo_id not in solicitudes_por_periodo:
                solicitudes_por_periodo[periodo_id] = []
            solicitudes_por_periodo[periodo_id].append(solicitud)
        
        for periodo in periodos:
            dias_habiles_disfrutados = 0
            dias_calendario_disfrutados = 0
            
            solicitudes_periodo = solicitudes_por_periodo.get(periodo.pk, [])
            for solicitud in solicitudes_periodo:
                habiles, calendario = self._calcular_dias_habiles_calendario_solicitud(solicitud)
                dias_habiles_disfrutados += habiles
                dias_calendario_disfrutados += calendario
            
            habiles_totales, calendario_totales = self._obtener_tipo_dias_periodo(periodo)
            dias_habiles_pendientes = max(0, habiles_totales - dias_habiles_disfrutados)
            dias_calendario_pendientes = max(0, calendario_totales - dias_calendario_disfrutados)
            dias_pendientes_reales = dias_habiles_pendientes + dias_calendario_pendientes
            
            if dias_pendientes_reales > 0:
                return True
        
        return False
    
    def _calcular_dias_habiles_calendario_solicitud(self, solicitud):
        """Calcula los días hábiles y calendario de una solicitud según el estamento."""
        if not (solicitud.fecha_inicio_vacaciones and solicitud.fecha_fin_vacaciones):
            return 0, 0
        
        estamento = solicitud.funcionario.estamento.nombre.lower()
        decreto = (solicitud.funcionario.decreto_resolucion or '').strip()
        
        festivos = holidays.Colombia(years=range(
            solicitud.fecha_inicio_vacaciones.year, 
            solicitud.fecha_fin_vacaciones.year + 1
        ))
        
        if estamento == 'docente' and decreto == '1279':
            actual = solicitud.fecha_inicio_vacaciones
            habiles_marcados = 0
            
            while actual <= solicitud.fecha_fin_vacaciones and habiles_marcados < 15:
                if actual.weekday() < 5 and actual not in festivos:
                    habiles_marcados += 1
                actual += timedelta(days=1)
            
            dias_calendario = 0
            while actual <= solicitud.fecha_fin_vacaciones and dias_calendario < 15:
                dias_calendario += 1
                actual += timedelta(days=1)
            
            return habiles_marcados, dias_calendario
            
        elif estamento == 'administrativo':
            actual = solicitud.fecha_inicio_vacaciones
            dias_habiles = 0
            while actual <= solicitud.fecha_fin_vacaciones:
                if actual.weekday() < 5 and actual not in festivos:
                    dias_habiles += 1
                actual += timedelta(days=1)
            return dias_habiles, 0
            
        elif estamento == 'docente' and decreto == '115':
            dias_calendario = (solicitud.fecha_fin_vacaciones - solicitud.fecha_inicio_vacaciones).days + 1
            return 0, dias_calendario
            
        elif estamento == 'trabajador oficial':
            dias_calendario = (solicitud.fecha_fin_vacaciones - solicitud.fecha_inicio_vacaciones).days + 1
            return 0, dias_calendario
            
        else:
            dias_calendario = (solicitud.fecha_fin_vacaciones - solicitud.fecha_inicio_vacaciones).days + 1
            return 0, dias_calendario
    
    def _obtener_tipo_dias_periodo(self, periodo):
        """Obtiene el tipo de días que otorga el periodo según el estamento."""
        estamento = periodo.funcionario.estamento.nombre.lower()
        decreto = (periodo.funcionario.decreto_resolucion or '').strip()
        
        if estamento == 'docente' and decreto == '1279':
            return 15, 15
        elif estamento == 'administrativo':
            return 15, 0
        elif estamento == 'docente' and decreto == '115':
            return 0, 30
        elif estamento == 'trabajador oficial':
            return 0, 30
        else:
            return 0, 0

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["rol_actual"] = "jefe_inmediato"
        context["mostrar_alerta_rol"] = user.groups.filter(name="Coordinador Administrativo").exists()
        context["etiqueta_rol_actual"] = "Jefe Inmediato"
        
        jefe_func = getattr(user, "funcionario", None)
        if jefe_func:
            context['jefe_id'] = jefe_func.pk
            
            periodos_jefe = PeriodoVacacional.objects.filter(funcionario=jefe_func)
            context['tiene_periodos'] = periodos_jefe.exists()
            
            context['tiene_periodos_disponibles'] = self._verificar_periodos_con_dias_disponibles(jefe_func)
            
            solicitudes_activas_jefe = SolicitudVacaciones.objects.filter(
                funcionario=jefe_func,
                estado_solicitud__in=['pendiente', 'en_revision', 'aprobado']
            ).prefetch_related('reintegrovacaciones_set')
            
            solicitudes_sin_reintegro_jefe = []
            for solicitud in solicitudes_activas_jefe:
                tiene_reintegro = any(
                    reintegro.estado_solicitud in ('aprobado', 'completado')
                    for reintegro in solicitud.reintegrovacaciones_set.all()
                )
                if not tiene_reintegro:
                    solicitudes_sin_reintegro_jefe.append(solicitud)
            
            context['tiene_solicitud_activa'] = len(solicitudes_sin_reintegro_jefe) > 0
            context['solicitud_activa'] = solicitudes_sin_reintegro_jefe[0] if solicitudes_sin_reintegro_jefe else None
            
            reintegros_en_curso_jefe = ReintegroVacaciones.objects.filter(
                funcionario=jefe_func,
                estado_solicitud__in=['pendiente', 'en_revision', 'devuelta']
            ).exists()
            context['tiene_reintegro_en_curso'] = reintegros_en_curso_jefe

            tiene_dias_pendientes_jefe = ReintegroVacaciones.objects.filter(
                funcionario=jefe_func,
                estado_solicitud='aprobado',
                dias_pendientes__gt=0
            ).exists()
            context['tiene_dias_pendientes_reintegro'] = tiene_dias_pendientes_jefe
            
            funcionarios_bajo_jefe = Funcionario.objects.filter(
                jefe_inmediato=jefe_func
            ).exclude(pk=jefe_func.pk).select_related('facultad_dependencia')
            
            funcionarios_data = []
            for func in funcionarios_bajo_jefe:
                solicitudes_activas_func = SolicitudVacaciones.objects.filter(
                    funcionario=func,
                    estado_solicitud__in=['pendiente', 'en_revision', 'aprobado']
                ).prefetch_related('reintegrovacaciones_set')
                
                solicitudes_sin_reintegro_func = []
                for solicitud in solicitudes_activas_func:
                    tiene_reintegro = any(
                        reintegro.estado_solicitud in ('aprobado', 'completado')
                        for reintegro in solicitud.reintegrovacaciones_set.all()
                    )
                    if not tiene_reintegro:
                        solicitudes_sin_reintegro_func.append(solicitud)
                
                tiene_periodos_func = PeriodoVacacional.objects.filter(funcionario=func).exists()
                
                tiene_periodos_disponibles_func = self._verificar_periodos_con_dias_disponibles(func)
                
                reintegros_en_curso_func = ReintegroVacaciones.objects.filter(
                    funcionario=func,
                    estado_solicitud__in=['pendiente', 'en_revision', 'devuelta']
                ).exists()
                
                tiene_dias_pendientes_func = ReintegroVacaciones.objects.filter(
                    funcionario=func,
                    estado_solicitud='aprobado',
                    dias_pendientes__gt=0
                ).exists()
                
                funcionarios_data.append({
                    'id': func.pk,
                    'nombre': func.nombre,
                    'apellido': func.apellido,
                    'facultad_dependencia': func.facultad_dependencia.nombre,
                    'tiene_solicitud_activa': len(solicitudes_sin_reintegro_func) > 0,
                    'solicitud_activa_codigo': solicitudes_sin_reintegro_func[0].codigo_sabs if solicitudes_sin_reintegro_func else None,
                    'tiene_periodos': tiene_periodos_func,
                    'tiene_periodos_disponibles': tiene_periodos_disponibles_func,
                    'tiene_reintegro_en_curso': reintegros_en_curso_func,
                    'tiene_dias_pendientes_reintegro': tiene_dias_pendientes_func
                })
            
            context['funcionarios_bajo_jefe'] = json.dumps(funcionarios_data)
        else:
            context['jefe_id'] = None
            context['tiene_periodos'] = False
            context['tiene_solicitud_activa'] = False
            context['tiene_reintegro_en_curso'] = False
            context['tiene_dias_pendientes_reintegro'] = False
            context['funcionarios_bajo_jefe'] = '[]'
        
        return context

def solicitud_pdf(request, pk):
    solicitud = get_object_or_404(SolicitudVacaciones, pk=pk)
    if not _es_jefe_de(solicitud, request.user) and not request.user.is_superuser:
        return HttpResponseForbidden()
    return redirect(solicitud.pdf_url)

@group_required("Jefe Inmediato", "Coordinador Administrativo")
def aprobar_solicitud(request, pk):
    if request.method != "POST":
        return HttpResponseBadRequest("Método no permitido")
    solicitud = get_object_or_404(SolicitudVacaciones, pk=pk)
    if not _es_jefe_de(solicitud, request.user) and not request.user.is_superuser:
        return HttpResponseForbidden()

    try:
        aprobar_etapa(request.user, solicitud, observacion=request.POST.get('obs', ''))
        messages.success(request, "Solicitud aprobada correctamente.")
    except (ValidationError, PermissionDenied) as e:
        messages.error(request, str(e))
    
    return redirect(reverse("vacaciones:jefe_solicitudes_list"))

@group_required("Jefe Inmediato", "Coordinador Administrativo")
def devolver_solicitud(request, pk):
    if request.method != "POST":
        return HttpResponseBadRequest("Método no permitido")
    solicitud = get_object_or_404(SolicitudVacaciones, pk=pk)
    if not _es_jefe_de(solicitud, request.user) and not request.user.is_superuser:
        return HttpResponseForbidden()

    try:
        devolver_etapa(request.user, solicitud, observacion=request.POST.get('obs', ''))
        messages.info(request, "Solicitud devuelta correctamente.")
    except (ValidationError, PermissionDenied) as e:
        messages.error(request, str(e))
    
    return redirect(reverse("vacaciones:jefe_solicitudes_list"))

@group_required("Jefe Inmediato", "Coordinador Administrativo")
def enviar_solicitud_proximo_revisor(request, pk):
    if request.method != "POST":
        return HttpResponseBadRequest("Método no permitido")
    solicitud = get_object_or_404(SolicitudVacaciones, pk=pk)
    if not _es_jefe_de(solicitud, request.user) and not request.user.is_superuser:
        return HttpResponseForbidden()

    try:
        enviar_al_proximo_revisor(request.user, solicitud, observacion=request.POST.get('obs', ''))
        messages.success(request, "Solicitud enviada al próximo revisor correctamente.")
    except (ValidationError, PermissionDenied) as e:
        messages.error(request, str(e))
    
    return redirect(reverse("vacaciones:jefe_solicitudes_list"))

@method_decorator(group_required("Jefe Inmediato", "Coordinador Administrativo"), name="dispatch")
class JefeSolicitudCreateView(LoginRequiredMixin, CreateView):
    """
    Permite al jefe crear solicitudes en nombre de funcionarios
    que tienen a él como jefe_inmediato.
    """
    model = SolicitudVacaciones
    form_class = SolicitudVacacionesForm
    template_name = JEFE_SOLICITUD_FORM_TEMPLATE
    success_url = reverse_lazy("vacaciones:jefe_solicitudes_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        
        funcionario_id = self.request.GET.get('funcionario_id')
        if funcionario_id:
            kwargs['funcionario_id'] = funcionario_id
        
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        hoy_colombia = get_current_date_colombia()
        initial['fecha_solicitud'] = hoy_colombia
        initial['codigo_sabs'] = generar_codigo_sabs('VAC', hoy_colombia.year)
        return initial

    def dispatch(self, request, *args, **kwargs):
        funcionario_id = request.GET.get('funcionario_id')
        if not funcionario_id:
            messages.error(request, "Debe seleccionar un funcionario para crear la solicitud.")
            return redirect("vacaciones:jefe_solicitudes_list")
        
        jefe_func = getattr(request.user, "funcionario", None)
        if not jefe_func:
            messages.error(request, "No se encontró información del funcionario asociado.")
            return redirect("vacaciones:jefe_solicitudes_list")
        
        try:
            funcionario_target = Funcionario.objects.get(pk=funcionario_id)
        except Funcionario.DoesNotExist:
            messages.error(request, "Funcionario no encontrado.")
            return redirect("vacaciones:jefe_solicitudes_list")
        
        if funcionario_target.jefe_inmediato != jefe_func:
            messages.error(request, "No tiene permisos para crear solicitudes para este funcionario.")
            return redirect("vacaciones:jefe_solicitudes_list")
        
        solicitudes_activas = SolicitudVacaciones.objects.filter(
            funcionario=funcionario_target,
            estado_solicitud__in=['pendiente', 'en_revision', 'aprobado']
        ).prefetch_related('reintegrovacaciones_set')
        
        solicitudes_sin_reintegro = []
        for solicitud in solicitudes_activas:
            tiene_reintegro = any(
                reintegro.estado_solicitud in ('aprobado', 'completado')
                for reintegro in solicitud.reintegrovacaciones_set.all()
            )
            if not tiene_reintegro:
                solicitudes_sin_reintegro.append(solicitud)
        
        if solicitudes_sin_reintegro:
            messages.error(
                request, 
                "El funcionario seleccionado ya tiene una solicitud de vacaciones activa y no puede crear otra."
            )
            return redirect("vacaciones:jefe_solicitudes_list")
        
        periodos_vacacionales = PeriodoVacacional.objects.filter(funcionario=funcionario_target)
        if not periodos_vacacionales.exists():
            messages.error(
                request,
                "El funcionario seleccionado no tiene periodos vacacionales registrados y no puede crear una solicitud."
            )
            return redirect("vacaciones:jefe_solicitudes_list")
        
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoy_colombia = get_current_date_colombia()
        years = [hoy_colombia.year, hoy_colombia.year + 1]
        festivos = []

        for y in years:
            festivos += [d.strftime('%d/%m/%Y') for d in holidays.Colombia(years=[y]).keys()]
        
        context['festivos_colombia'] = json.dumps(festivos)

        funcionario_id = self.request.GET.get('funcionario_id')
        try:
            funcionario = Funcionario.objects.get(pk=funcionario_id)
        except Funcionario.DoesNotExist:
            funcionario = None
        
        if funcionario:
            context['funcionario_target'] = funcionario
            context['funcionario_estamento'] = funcionario.estamento.nombre.lower()
            context['funcionario_decreto'] = (funcionario.decreto_resolucion or '').strip()

            periodos_vacacionales = PeriodoVacacional.objects.filter(funcionario=funcionario)
            context['tiene_periodos_vacacionales'] = periodos_vacacionales.exists()
            
            periodos_dias_pendientes = {}
            for periodo in periodos_vacacionales:
                periodos_dias_pendientes[periodo.pk] = periodo.dias_pendientes_periodo
            context['periodos_dias_pendientes'] = json.dumps(periodos_dias_pendientes)
            
            reintegros_pendientes = ReintegroVacaciones.objects.filter(
                funcionario=funcionario,
                estado_solicitud='aprobado',
                dias_pendientes__gt=0
            )

            reintegros_data = []
            for reintegro in reintegros_pendientes:
                reintegros_data.append({
                    'id': reintegro.id,
                    'dias_pendientes': reintegro.dias_pendientes,
                    'tipo_dias': reintegro.tipo_dias_pendientes,
                    'periodo_vacacional_id': reintegro.periodo_vacacional_id,
                    'fecha_disfrute_desde': reintegro.fecha_disfrute_desde.strftime('%d/%m/%Y'),
                    'fecha_disfrute_hasta': reintegro.fecha_disfrute_hasta.strftime('%d/%m/%Y')
                })

            context['reintegros_pendientes'] = json.dumps(reintegros_data)
            context['tiene_reintegros_pendientes'] = len(reintegros_data) > 0

        form = context.get('form')
        context['mostrar_alerta_periodos_acumulados'] = False
        
        if hasattr(form, 'periodos_acumulados') and form.periodos_acumulados:
            context['periodos_acumulados'] = form.periodos_acumulados
            context['periodo_mas_antiguo'] = form.periodo_mas_antiguo
            context['periodo_mas_reciente'] = form.periodo_mas_reciente
            context['periodo_mas_antiguo_habilitado'] = form.periodo_mas_antiguo_habilitado
            context['periodo_mas_reciente_habilitado'] = form.periodo_mas_reciente_habilitado
            
            if funcionario:
                solicitudes_periodos_acumulados = SolicitudVacaciones.objects.filter(
                    funcionario=funcionario,
                    periodo_vacacional__in=[form.periodo_mas_antiguo, form.periodo_mas_reciente],
                    estado_solicitud__in=['pendiente', 'en_revision', 'aprobado', 'devuelta']
                ).exists()
                context['mostrar_alerta_periodos_acumulados'] = not solicitudes_periodos_acumulados

        context["rol_actual"] = "jefe_inmediato"
        context["mostrar_alerta_rol"] = self.request.user.groups.filter(name="Coordinador Administrativo").exists()
        context["etiqueta_rol_actual"] = "Jefe Inmediato"

        return context

    def post(self, request, *args, **kwargs):
        self.object = None
        funcionario_id = request.GET.get('funcionario_id')
        
        if not funcionario_id:
            messages.error(request, "Debe seleccionar un funcionario para crear la solicitud.")
            return self.form_invalid(self.get_form())

        try:
            funcionario_target = Funcionario.objects.get(pk=funcionario_id)
        except Funcionario.DoesNotExist:
            messages.error(request, "Funcionario no encontrado.")
            return self.form_invalid(self.get_form())

        jefe_func = getattr(request.user, "funcionario", None)
        if not jefe_func:
            messages.error(request, "No se encontró información del funcionario asociado.")
            return self.form_invalid(self.get_form())

        if funcionario_target.jefe_inmediato != jefe_func:
            messages.error(request, "No tiene permisos para crear solicitudes para este funcionario.")
            return self.form_invalid(self.get_form())

        periodos_vacacionales = PeriodoVacacional.objects.filter(funcionario=funcionario_target)
        if not periodos_vacacionales.exists():
            messages.error(request, "No puede crear una solicitud de vacaciones sin tener periodos vacacionales registrados.")
            return self.form_invalid(self.get_form())

        solicitudes_activas = SolicitudVacaciones.objects.filter(
            funcionario=funcionario_target,
            estado_solicitud__in=['pendiente', 'en_revision', 'aprobado']
        ).prefetch_related('reintegrovacaciones_set')
        
        solicitudes_sin_reintegro = []
        for solicitud in solicitudes_activas:
            tiene_reintegro = any(
                reintegro.estado_solicitud in ('aprobado', 'completado')
                for reintegro in solicitud.reintegrovacaciones_set.all()
            )
            if not tiene_reintegro:
                solicitudes_sin_reintegro.append(solicitud)
        
        if solicitudes_sin_reintegro:
            messages.error(request, "El funcionario seleccionado ya tiene una solicitud de vacaciones activa y no puede crear otra.")
            return self.form_invalid(self.get_form())

        form = self.get_form()
        form.instance.funcionario = funcionario_target
        
        hoy_colombia = get_current_date_colombia()
        form.instance.fecha_solicitud = hoy_colombia
        
        if form.is_valid():
            return self.form_valid(form)
        
        return self.form_invalid(form)

    def form_valid(self, form):
        try:
            self.object = form.save()
            messages.success(self.request, "Solicitud registrada correctamente.")
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f"Error al guardar la solicitud: {e}")
            return self.form_invalid(form)

@method_decorator(group_required("Jefe Inmediato", "Coordinador Administrativo"), name="dispatch")
class ReintegrosJefeListView(LoginRequiredMixin, ListView):
    """
    Lista los reintegros de vacaciones que el jefe puede ver:
    - De funcionarios que tienen el mismo jefe_inmediato que él
    - Incluye todas las solicitudes de reintegro de los subordinados
    """
    model = ReintegroVacaciones
    template_name = JEFE_REINTEGROS_TEMPLATE
    context_object_name = "reintegros"
    paginate_by = 20

    def get(self, request, *args, **kwargs):
        if request.htmx:
            self.object_list = self.get_queryset()
            context = self.get_context_data()
            html = render_to_string(JEFE_REINTEGROS_TABLE_PARTIAL, context, request)
            return HttpResponse(html)
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        jefe_func = getattr(self.request.user, "funcionario", None)

        if not jefe_func:
            return ReintegroVacaciones.objects.none()

        qs = (ReintegroVacaciones.objects
              .select_related("funcionario", "funcionario__facultad_dependencia", "creada_por", "creada_por__funcionario", "solicitud_vacaciones", "periodo_vacacional")
              .prefetch_related("aprobaciones")
              .filter(funcionario__jefe_inmediato=jefe_func)
              .exclude(estado_solicitud='pendiente')
              .order_by("-fecha_solicitud", "-id"))

        q = self.request.GET.get("q", "").strip()
        estado = self.request.GET.get("estado", "").strip()

        if q:
            qs = qs.filter(
                Q(codigo_sabs__icontains=q) |
                Q(funcionario__nombre__icontains=q) |
                Q(funcionario__apellido__icontains=q)
            )
        if estado:
            qs = qs.filter(estado_solicitud=estado)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["rol_actual"] = "jefe_inmediato"
        context["mostrar_alerta_rol"] = user.groups.filter(name="Coordinador Administrativo").exists()
        context["etiqueta_rol_actual"] = "Jefe Inmediato"
        
        jefe_func = getattr(self.request.user, "funcionario", None)
        if jefe_func:
            funcionarios_bajo_jefe = Funcionario.objects.filter(
                jefe_inmediato=jefe_func
            ).select_related('facultad_dependencia')
            
            funcionarios_data = []
            
            solicitudes_jefe = ReintegroVacacionesListView._solicitudes_autorizadas_sin_reintegro(jefe_func)
            funcionarios_data.append({
                'id': jefe_func.pk,
                'nombre': jefe_func.nombre,
                'apellido': jefe_func.apellido,
                'facultad_dependencia': jefe_func.facultad_dependencia.nombre if jefe_func.facultad_dependencia else '',
                'tiene_solicitudes_autorizadas': len(solicitudes_jefe) > 0,
                'solicitudes_autorizadas': [
                    {
                        'id': sol.pk,
                        'codigo_sabs': sol.codigo_sabs,
                        'fecha_inicio': sol.fecha_inicio_vacaciones.strftime('%d/%m/%Y'),
                        'fecha_fin': sol.fecha_fin_vacaciones.strftime('%d/%m/%Y')
                    }
                    for sol in solicitudes_jefe
                ]
            })
            
            for func in funcionarios_bajo_jefe:
                solicitudes_disponibles = ReintegroVacacionesListView._solicitudes_autorizadas_sin_reintegro(func)
                
                funcionarios_data.append({
                    'id': func.pk,
                    'nombre': func.nombre,
                    'apellido': func.apellido,
                    'facultad_dependencia': func.facultad_dependencia.nombre if func.facultad_dependencia else '',
                    'tiene_solicitudes_autorizadas': len(solicitudes_disponibles) > 0,
                    'solicitudes_autorizadas': [
                        {
                            'id': sol.pk,
                            'codigo_sabs': sol.codigo_sabs,
                            'fecha_inicio': sol.fecha_inicio_vacaciones.strftime('%d/%m/%Y'),
                            'fecha_fin': sol.fecha_fin_vacaciones.strftime('%d/%m/%Y')
                        }
                        for sol in solicitudes_disponibles
                    ]
                })
            
            context["funcionarios_bajo_jefe"] = json.dumps(funcionarios_data)
        else:
            context["funcionarios_bajo_jefe"] = json.dumps([])

        return context


@group_required("Jefe Inmediato", "Coordinador Administrativo")
def aprobar_reintegro(request, pk):
    if request.method != "POST":
        return HttpResponseBadRequest("Método no permitido")
    reintegro = get_object_or_404(ReintegroVacaciones, pk=pk)
    if not _es_jefe_de_reintegro(reintegro, request.user) and not request.user.is_superuser:
        return HttpResponseForbidden()

    try:
        aprobar_etapa_reintegro(request.user, reintegro, observacion=request.POST.get('obs', ''))
        messages.success(request, "Reintegro aprobado correctamente.")
    except (ValidationError, PermissionDenied) as e:
        messages.error(request, str(e))
    
    return redirect(reverse("vacaciones:jefe_reintegros_list"))


@group_required("Jefe Inmediato", "Coordinador Administrativo")
def devolver_reintegro(request, pk):
    if request.method != "POST":
        return HttpResponseBadRequest("Método no permitido")
    reintegro = get_object_or_404(ReintegroVacaciones, pk=pk)
    if not _es_jefe_de_reintegro(reintegro, request.user) and not request.user.is_superuser:
        return HttpResponseForbidden()

    try:
        devolver_etapa_reintegro(request.user, reintegro, observacion=request.POST.get('obs', ''))
        messages.info(request, "Reintegro devuelto correctamente.")
    except (ValidationError, PermissionDenied) as e:
        messages.error(request, str(e))
    
    return redirect(reverse("vacaciones:jefe_reintegros_list"))


@method_decorator(group_required("Jefe Inmediato", "Coordinador Administrativo"), name="dispatch")
class JefeReintegroCreateView(LoginRequiredMixin, CreateView):
    """
    Permite al jefe crear reintegros en nombre de funcionarios
    que tienen a él como jefe_inmediato.
    """
    model = ReintegroVacaciones
    form_class = ReintegroVacacionesForm
    template_name = JEFE_REINTEGRO_FORM_TEMPLATE
    success_url = reverse_lazy("vacaciones:jefe_reintegros_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        
        funcionario_id = self.request.GET.get('funcionario_id')
        if funcionario_id:
            kwargs['funcionario_id'] = funcionario_id
        
        solicitud_id = self.request.GET.get('solicitud_id')
        if solicitud_id:
            kwargs['solicitud_id'] = solicitud_id
        
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        hoy_colombia = get_current_date_colombia()
        initial['fecha_solicitud'] = hoy_colombia
        initial['codigo_sabs'] = generar_codigo_sabs('REI', hoy_colombia.year)
        
        solicitud_id = self.request.GET.get('solicitud_id')
        if solicitud_id:
            try:
                solicitud = SolicitudVacaciones.objects.get(pk=solicitud_id)
                initial['solicitud_vacaciones'] = solicitud
                initial['fecha_disfrute_desde'] = solicitud.fecha_inicio_vacaciones
                initial['fecha_disfrute_hasta'] = solicitud.fecha_fin_vacaciones
                initial['periodo_correspondiente_desde'] = solicitud.periodo_vacacional.fecha_inicio_periodo
                initial['periodo_correspondiente_hasta'] = solicitud.periodo_vacacional.fecha_fin_periodo
            except SolicitudVacaciones.DoesNotExist:
                pass
        
        return initial

    def dispatch(self, request, *args, **kwargs):
        funcionario_id = request.GET.get('funcionario_id')
        if not funcionario_id:
            messages.error(request, "Debe seleccionar un funcionario para crear el reintegro.")
            return redirect("vacaciones:jefe_reintegros_list")
        
        jefe_func = getattr(request.user, "funcionario", None)
        if not jefe_func:
            messages.error(request, "No se encontró información del funcionario asociado.")
            return redirect("vacaciones:jefe_reintegros_list")
        
        try:
            funcionario_target = Funcionario.objects.get(pk=funcionario_id)
        except Funcionario.DoesNotExist:
            messages.error(request, "Funcionario no encontrado.")
            return redirect("vacaciones:jefe_reintegros_list")
        
        if funcionario_target.jefe_inmediato != jefe_func:
            messages.error(request, "No tiene permisos para crear reintegros para este funcionario.")
            return redirect("vacaciones:jefe_reintegros_list")
        
        solicitudes_disponibles = ReintegroVacacionesListView._solicitudes_autorizadas_sin_reintegro(funcionario_target)
        
        if not solicitudes_disponibles:
            messages.error(
                request,
                "El funcionario seleccionado no tiene solicitudes de vacaciones autorizadas disponibles para reintegro."
            )
            return redirect("vacaciones:jefe_reintegros_list")
        
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoy_colombia = get_current_date_colombia()
        years = [hoy_colombia.year, hoy_colombia.year + 1]
        festivos = []

        for y in years:
            festivos += [d.strftime('%d/%m/%Y') for d in holidays.Colombia(years=[y]).keys()]
        
        context['festivos_colombia'] = json.dumps(festivos)

        funcionario_id = self.request.GET.get('funcionario_id')
        try:
            funcionario = Funcionario.objects.get(pk=funcionario_id)
        except Funcionario.DoesNotExist:
            funcionario = None
        
        if funcionario:
            context['funcionario_target'] = funcionario
            context['funcionario_estamento'] = funcionario.estamento.nombre.lower()
            context['funcionario_decreto'] = (funcionario.decreto_resolucion or '').strip()

        context["rol_actual"] = "jefe_inmediato"
        context["mostrar_alerta_rol"] = self.request.user.groups.filter(name="Coordinador Administrativo").exists()
        context["etiqueta_rol_actual"] = "Jefe Inmediato"

        return context

    def post(self, request, *args, **kwargs):
        self.object = None
        funcionario_id = request.GET.get('funcionario_id')
        
        if not funcionario_id:
            messages.error(request, "Debe seleccionar un funcionario para crear el reintegro.")
            return self.form_invalid(self.get_form())

        try:
            funcionario_target = Funcionario.objects.get(pk=funcionario_id)
        except Funcionario.DoesNotExist:
            messages.error(request, "Funcionario no encontrado.")
            return self.form_invalid(self.get_form())

        jefe_func = getattr(request.user, "funcionario", None)
        if not jefe_func:
            messages.error(request, "No se encontró información del funcionario asociado.")
            return self.form_invalid(self.get_form())

        if funcionario_target.jefe_inmediato != jefe_func:
            messages.error(request, "No tiene permisos para crear reintegros para este funcionario.")
            return self.form_invalid(self.get_form())

        form = self.get_form()
        form.instance.funcionario = funcionario_target
        
        hoy_colombia = get_current_date_colombia()
        form.instance.fecha_solicitud = hoy_colombia
        
        if form.is_valid():
            return self.form_valid(form)
        
        return self.form_invalid(form)

    def form_valid(self, form):
        try:
            self.object = form.save()
            self.object.creada_por = self.request.user
            self.object.save()
            messages.success(self.request, "Reintegro registrado correctamente.")
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f"Error al guardar el reintegro: {e}")
            return self.form_invalid(form)
