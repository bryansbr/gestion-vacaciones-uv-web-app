import holidays
import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView

from core.permissions import group_required
from usuarios.models import Funcionario
from .forms import SolicitudVacacionesForm
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
from .utils import get_current_date_colombia

# ==========================================================
# CONSTANTES
# ==========================================================
JEFE_SOLICITUDES_TEMPLATE = "vacaciones/roles/jefe/jefe-solicitudes-list.html"
JEFE_SOLICITUDES_TABLE_PARTIAL = "vacaciones/partials/_tabla-jefe-solicitudes.html"
JEFE_SOLICITUD_FORM_TEMPLATE = "vacaciones/roles/jefe/jefe-solicitud-form.html"

def _es_jefe_de(solicitud, user):
    user_func = getattr(user, "funcionario", None)
    if not user_func:
        return False
    return solicitud.funcionario.jefe_inmediato_id == user_func.pk

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
    paginate_by = 20

    def get(self, request, *args, **kwargs):
        if request.htmx:
            self.object_list = self.get_queryset()
            context = self.get_context_data()
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
                reintegro.estado_solicitud == 'aprobado' 
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
                    periodo_vacacional__in=[form.periodo_mas_antiguo, form.periodo_mas_reciente]
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
                reintegro.estado_solicitud == 'aprobado' 
                for reintegro in solicitud.reintegrovacaciones_set.all()
            )
            if not tiene_reintegro:
                solicitudes_sin_reintegro.append(solicitud)
        
        if solicitudes_sin_reintegro:
            messages.error(request, "El funcionario seleccionado ya tiene una solicitud de vacaciones activa y no puede crear otra.")
            return self.form_invalid(self.get_form())

        form = self.get_form()
        form.instance.funcionario = funcionario_target
        form.instance.creada_por = request.user
        
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
