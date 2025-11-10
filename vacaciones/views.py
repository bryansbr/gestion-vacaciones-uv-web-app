import holidays
import json
import urllib.parse

from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from weasyprint import HTML

from core.permissions import group_required, es_secretaria, es_jefe_inmediato, es_coordinador_administrativo, es_rrhh
from .forms import PeriodoVacacionalForm, SolicitudVacacionesForm
from .models import (
    AprobacionEtapa,
    PeriodoVacacional,
    ReintegroVacaciones,
    SolicitudVacaciones,
    generar_codigo_sabs
)
from .services.aprobaciones import (
    aprobar_etapa,
    autorizar_rrhh,
    devolver_etapa,
    rechazar_rrhh,
    reenviar_funcionario
)
from .utils import get_current_date_colombia, puede_solicitar_vacaciones_hoy
from usuarios.models import Funcionario

# ==========================================================
# CONSTANTES
# ==========================================================
PERIODO_VACACIONAL_LIST_TEMPLATE = "vacaciones/prd-vac/periodo-vacacional-list.html"
PERIODO_VACACIONAL_FORM_TEMPLATE = "vacaciones/prd-vac/periodo-vacacional-form.html"
PERIODO_VACACIONAL_CONFIRM_DELETE_TEMPLATE = "vacaciones/prd-vac/periodo-vacacional-confirm-delete.html"
TABLA_PERIODOS_VACACIONALES_PARTIAL = "vacaciones/partials/_tabla-periodos-vacacionales.html"

SOLICITUD_VACACIONES_FORM_TEMPLATE = "vacaciones/solicitud-vac/solicitud-vacaciones-form.html"
SOLICITUD_VACACIONES_LIST_TEMPLATE = "vacaciones/solicitud-vac/solicitud-vacaciones-list.html"
SOLICITUD_VACACIONES_CONFIRM_DELETE_TEMPLATE = "vacaciones/solicitud-vac/solicitud-vacaciones-confirm-delete.html"
TABLA_FUNCIONARIO_SOLICITUDES_PARTIAL = "vacaciones/partials/_tabla-funcionario-solicitudes.html"
SEMAFORO_CELL_PARTIAL = "vacaciones/partials/_semaforo-cell.html"
SOLICITUD_VACACIONES_PDF_TEMPLATE = "vacaciones/pdf/solicitud-vacaciones.html"

SECRETARIA_SOLICITUDES_LIST_TEMPLATE = "vacaciones/roles/secretaria/secretaria-solicitudes-list.html"
SECRETARIA_SOLICITUD_FORM_TEMPLATE = "vacaciones/roles/secretaria/secretaria-solicitud-form.html"
SECRETARIA_SOLICIT_CONFIRM_DELETE_TEMPLATE = "vacaciones/roles/secretaria/secretaria-solicitud-confirm-delete.html"
TABLA_SECRETARIA_SOLICITUDES_PARTIAL = "vacaciones/partials/_tabla-secretaria-solicitudes.html"

# -----------------------------------------
# VISTA: PeriodoVacacional
# -----------------------------------------
class PeriodoVacacionalListView(LoginRequiredMixin, ListView):
    model = PeriodoVacacional
    template_name = PERIODO_VACACIONAL_LIST_TEMPLATE
    context_object_name = "periodos"
    paginate_by = 20

    def get(self, request, *args, **kwargs):
        if request.htmx:
            self.object_list = self.get_queryset()
            context = self.get_context_data()
            html = render_to_string(TABLA_PERIODOS_VACACIONALES_PARTIAL, context, request)
            return HttpResponse(html)
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        qs = PeriodoVacacional.objects.select_related('funcionario').order_by('-fecha_inicio_periodo')
        
        q = self.request.GET.get("q", "").strip()
        
        if q:
            qs = qs.filter(
                Q(funcionario__nombre__icontains=q) |
                Q(funcionario__apellido__icontains=q) |
                Q(funcionario__numero_identificacion__icontains=q)
            )

        return qs

class PeriodoVacacionalCreateView(LoginRequiredMixin, CreateView):
    model = PeriodoVacacional
    form_class = PeriodoVacacionalForm
    template_name = PERIODO_VACACIONAL_FORM_TEMPLATE
    success_url = reverse_lazy("vacaciones:periodo-vacacional-list")

    def form_valid(self, form):
        messages.success(self.request, "Periodo vacacional creado correctamente.")
        return super().form_valid(form)

class PeriodoVacacionalUpdateView(LoginRequiredMixin, UpdateView):
    model = PeriodoVacacional
    form_class = PeriodoVacacionalForm
    template_name = PERIODO_VACACIONAL_FORM_TEMPLATE
    success_url = reverse_lazy("vacaciones:periodo-vacacional-list")

    def form_valid(self, form):
        messages.success(self.request, "Periodo vacacional actualizado correctamente.")
        return super().form_valid(form)

class PeriodoVacacionalDeleteView(LoginRequiredMixin, DeleteView):
    model = PeriodoVacacional
    template_name = PERIODO_VACACIONAL_CONFIRM_DELETE_TEMPLATE
    success_url = reverse_lazy("vacaciones:periodo-vacacional-list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Periodo vacacional eliminado correctamente.")
        return super().delete(request, *args, **kwargs)

# -----------------------------------------
# VISTA: Crear SolicitudVacaciones
# -----------------------------------------
class SolicitudVacacionesCreateView(LoginRequiredMixin, CreateView):
    model = SolicitudVacaciones
    form_class = SolicitudVacacionesForm
    template_name = SOLICITUD_VACACIONES_FORM_TEMPLATE
    success_url = reverse_lazy("vacaciones:solicitud-vacaciones-list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['initial'] = kwargs.get('initial', {})
        kwargs['initial']['user_id'] = self.request.user.id
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        hoy_colombia = get_current_date_colombia()
        initial['fecha_solicitud'] = hoy_colombia
        initial['codigo_sabs'] = generar_codigo_sabs('VAC', hoy_colombia.year)
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoy_colombia = get_current_date_colombia()
        years = [hoy_colombia.year, hoy_colombia.year + 1]
        festivos = []

        for y in years:
            festivos += [d.strftime('%d/%m/%Y') for d in holidays.Colombia(years=[y]).keys()]
        
        context['festivos_colombia'] = json.dumps(festivos)

        funcionario = self.request.user.funcionario
        context['funcionario_estamento'] = funcionario.estamento.nombre.lower()
        context['funcionario_decreto'] = (funcionario.decreto_resolucion or '').strip()

        periodos_vacacionales = PeriodoVacacional.objects.filter(funcionario=funcionario)
        context['tiene_periodos_vacacionales'] = periodos_vacacionales.exists()
        
        periodos_dias_pendientes = {}
        for periodo in periodos_vacacionales:
            periodos_dias_pendientes[periodo.pk] = periodo.dias_pendientes_periodo
        context['periodos_dias_pendientes'] = json.dumps(periodos_dias_pendientes)
        
        puede_solicitar_hoy, mensaje_plazo = puede_solicitar_vacaciones_hoy(
            funcionario.estamento.nombre.lower(),
            funcionario.decreto_resolucion
        )
        context['puede_solicitar_hoy'] = puede_solicitar_hoy
        context['mensaje_plazo'] = mensaje_plazo
        
        if not context['tiene_periodos_vacacionales']:
            context['reintegros_pendientes'] = json.dumps([])
            context['tiene_reintegros_pendientes'] = False
            context['periodos_acumulados'] = None
            context['plazo_solicitud'] = mensaje_plazo
            context['mostrar_alerta_periodos_acumulados'] = False
            context['periodos_dias_pendientes'] = json.dumps({})
            return context

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
        
        if context['tiene_reintegros_pendientes']:
            context['form'].initial['tiene_dias_pendientes'] = False

        solicitudes_activas_qs = SolicitudVacaciones.objects.filter(
            funcionario=funcionario,
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
        
        context['puede_crear_solicitud'] = len(solicitudes_sin_reintegro) == 0
        context['solicitud_activa'] = solicitudes_sin_reintegro[0] if solicitudes_sin_reintegro else None

        form = context.get('form')

        context['mostrar_alerta_periodos_acumulados'] = False
        
        if hasattr(form, 'periodos_acumulados') and form.periodos_acumulados:
            context['periodos_acumulados'] = form.periodos_acumulados
            context['periodo_mas_antiguo'] = form.periodo_mas_antiguo
            context['periodo_mas_reciente'] = form.periodo_mas_reciente
            context['periodo_mas_antiguo_habilitado'] = form.periodo_mas_antiguo_habilitado
            context['periodo_mas_reciente_habilitado'] = form.periodo_mas_reciente_habilitado
            
            if context['puede_crear_solicitud']:
                solicitudes_periodos_acumulados = SolicitudVacaciones.objects.filter(
                    funcionario=funcionario,
                    periodo_vacacional__in=[form.periodo_mas_antiguo, form.periodo_mas_reciente],
                    estado_solicitud__in=['pendiente', 'en_revision', 'aprobado', 'devuelta']
                ).exists()
                context['mostrar_alerta_periodos_acumulados'] = not solicitudes_periodos_acumulados

        context['plazo_solicitud'] = mensaje_plazo
        
        solicitud_rechazada = None
        if context.get('tiene_periodos_vacacionales'):
            base_rechazadas = SolicitudVacaciones.objects.filter(
                funcionario=funcionario,
                estado_solicitud='rechazado'
            )
            if solicitudes_activas_qs.exists():
                base_rechazadas = base_rechazadas.filter(
                    fecha_solicitud__gte=solicitudes_activas_qs.order_by('-fecha_solicitud').first().fecha_solicitud
                )
            solicitud_rechazada = base_rechazadas.order_by('-fecha_solicitud').first()

        context['solicitud_rechazada_reciente'] = solicitud_rechazada

        return context

    def post(self, request, *args, **kwargs):
        self.object = None
        funcionario = self.request.user.funcionario
        periodos_vacacionales = PeriodoVacacional.objects.filter(funcionario=funcionario)
        
        if not periodos_vacacionales.exists():
            messages.error(request, "No puede crear una solicitud de vacaciones sin tener periodos vacacionales registrados.")
            return self.form_invalid(self.get_form())

        solicitudes_activas = SolicitudVacaciones.objects.filter(
            funcionario=funcionario,
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
            messages.error(request, "Ya tiene una solicitud de vacaciones activa. Debe culminar el disfrute del periodo actual antes de crear una nueva solicitud.")
            return self.form_invalid(self.get_form())

        form = self.get_form()
        form.instance.funcionario = funcionario
        
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

    def get_success_url(self):
        url = super().get_success_url()
        separador = '&' if ('?' in url) else '?'
        codigo = getattr(self.object, 'codigo_sabs', '') or ''
        codigo_q = urllib.parse.quote(codigo)
        return f"{url}{separador}creada=1&codigo={codigo_q}"
    
class SolicitudVacacionesListView(LoginRequiredMixin, ListView):
    model = SolicitudVacaciones
    template_name = SOLICITUD_VACACIONES_LIST_TEMPLATE
    context_object_name = "solicitudes"
    paginate_by = 20

    def get(self, request, *args, **kwargs):
        if request.htmx:
            self.object_list = self.get_queryset()
            context = self.get_context_data()
            html = render_to_string(TABLA_FUNCIONARIO_SOLICITUDES_PARTIAL, context, request)
            return HttpResponse(html)
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if es_secretaria(self.request.user):
            qs = SolicitudVacaciones.objects.filter(creada_por=self.request.user).order_by('-fecha_solicitud')
        elif es_jefe_inmediato(self.request.user):
            qs = SolicitudVacaciones.objects.filter(
                Q(funcionario=self.request.user.funcionario) | Q(creada_por=self.request.user)
            ).distinct().order_by('-fecha_solicitud')
        elif es_coordinador_administrativo(self.request.user):
            qs = SolicitudVacaciones.objects.filter(
                Q(funcionario=self.request.user.funcionario) | Q(creada_por=self.request.user)
            ).distinct().order_by('-fecha_solicitud')
        else:
            qs = SolicitudVacaciones.objects.filter(funcionario=self.request.user.funcionario).order_by('-fecha_solicitud')
        
        qs = qs.select_related('funcionario', 'periodo_vacacional', 'creada_por', 'creada_por__funcionario')
        
        q = self.request.GET.get("q", "").strip()
        estado = self.request.GET.get("estado", "").strip()

        if q:
            if es_secretaria(self.request.user) or es_jefe_inmediato(self.request.user) or es_coordinador_administrativo(self.request.user):
                qs = qs.filter(
                    Q(codigo_sabs__icontains=q) |
                    Q(funcionario__nombre__icontains=q) |
                    Q(funcionario__apellido__icontains=q)
                )
            else:
                qs = qs.filter(codigo_sabs__icontains=q)
        if estado:
            qs = qs.filter(estado_solicitud=estado)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        funcionario = self.request.user.funcionario
        
        if es_secretaria(self.request.user) or es_jefe_inmediato(self.request.user) or es_coordinador_administrativo(self.request.user):
            context['puede_crear_solicitud'] = True
            
            solicitudes_activas = SolicitudVacaciones.objects.filter(
                funcionario=funcionario,
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
            
            context['solicitud_activa'] = solicitudes_sin_reintegro[0] if solicitudes_sin_reintegro else None
            context['tiene_solicitud_activa'] = len(solicitudes_sin_reintegro) > 0
            context['mensaje_plazo'] = None
            context['tiene_periodos'] = PeriodoVacacional.objects.filter(funcionario=funcionario).exists()
        else:
            solicitudes_activas = SolicitudVacaciones.objects.filter(
                funcionario=funcionario,
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

            context['puede_crear_solicitud'] = len(solicitudes_sin_reintegro) == 0
            context['solicitud_activa'] = solicitudes_sin_reintegro[0] if solicitudes_sin_reintegro else None
            context['mensaje_plazo'] = None
            
            context['tiene_periodos'] = PeriodoVacacional.objects.filter(funcionario=funcionario).exists()
        
        if es_secretaria(self.request.user):
            secretaria_func = self.request.user.funcionario
            
            if secretaria_func and secretaria_func.jefe_inmediato:
                funcionarios_bajo_jefe = Funcionario.objects.filter(
                    jefe_inmediato=secretaria_func.jefe_inmediato
                ).exclude(pk=secretaria_func.pk).select_related('facultad_dependencia')
                
                funcionarios_data = []
                for func in funcionarios_bajo_jefe:
                    solicitudes_activas_func = SolicitudVacaciones.objects.filter(
                        funcionario=func,
                        estado_solicitud__in=['pendiente', 'en_revision', 'aprobado']
                    ).prefetch_related('reintegrovacaciones_set')
                    
                    solicitudes_sin_reintegro_func = []
                    for solicitud in solicitudes_activas_func:
                        tiene_reintegro = any(
                            reintegro.estado_solicitud == 'aprobado' 
                            for reintegro in solicitud.reintegrovacaciones_set.all()
                        )
                        if not tiene_reintegro:
                            solicitudes_sin_reintegro_func.append(solicitud)
                    
                    tiene_periodos_func = PeriodoVacacional.objects.filter(funcionario=func).exists()
                    
                    funcionarios_data.append({
                        'id': func.pk,
                        'nombre': func.nombre,
                        'apellido': func.apellido,
                        'facultad_dependencia': func.facultad_dependencia.nombre,
                        'tiene_solicitud_activa': len(solicitudes_sin_reintegro_func) > 0,
                        'solicitud_activa_codigo': solicitudes_sin_reintegro_func[0].codigo_sabs if solicitudes_sin_reintegro_func else None,
                        'tiene_periodos': tiene_periodos_func
                    })
                
                context['funcionarios_bajo_jefe'] = json.dumps(funcionarios_data)
                context['secretaria_id'] = secretaria_func.pk
            else:
                context['funcionarios_bajo_jefe'] = '[]'
                context['secretaria_id'] = None
        
        if es_jefe_inmediato(self.request.user):
            jefe_func = self.request.user.funcionario
            
            if jefe_func:
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
                            reintegro.estado_solicitud == 'aprobado' 
                            for reintegro in solicitud.reintegrovacaciones_set.all()
                        )
                        if not tiene_reintegro:
                            solicitudes_sin_reintegro_func.append(solicitud)
                    
                    tiene_periodos_func = PeriodoVacacional.objects.filter(funcionario=func).exists()
                    
                    funcionarios_data.append({
                        'id': func.pk,
                        'nombre': func.nombre,
                        'apellido': func.apellido,
                        'facultad_dependencia': func.facultad_dependencia.nombre,
                        'tiene_solicitud_activa': len(solicitudes_sin_reintegro_func) > 0,
                        'solicitud_activa_codigo': solicitudes_sin_reintegro_func[0].codigo_sabs if solicitudes_sin_reintegro_func else None,
                        'tiene_periodos': tiene_periodos_func
                    })
                
                context['funcionarios_bajo_jefe'] = json.dumps(funcionarios_data)
                context['jefe_id'] = jefe_func.pk
            else:
                context['funcionarios_bajo_jefe'] = '[]'
                context['jefe_id'] = None
        
        return context

class SolicitudVacacionesUpdateView(LoginRequiredMixin, UpdateView):
    model = SolicitudVacaciones
    form_class = SolicitudVacacionesForm
    template_name = SOLICITUD_VACACIONES_FORM_TEMPLATE
    success_url = reverse_lazy("vacaciones:solicitud-vacaciones-list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['initial'] = kwargs.get('initial', {})
        kwargs['initial']['user_id'] = self.request.user.id
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        years = [get_current_date_colombia().year, get_current_date_colombia().year + 1]
        festivos = []

        for y in years:
            festivos += [d.strftime('%d/%m/%Y') for d in holidays.Colombia(years=[y]).keys()]
        
        context['festivos_colombia'] = json.dumps(festivos)

        funcionario = self.request.user.funcionario
        context['funcionario_estamento'] = funcionario.estamento.nombre.lower()
        context['funcionario_decreto'] = (funcionario.decreto_resolucion or '').strip()

        # Verificar si el funcionario tiene periodos vacacionales
        periodos_vacacionales = PeriodoVacacional.objects.filter(funcionario=funcionario)
        context['tiene_periodos_vacacionales'] = periodos_vacacionales.exists()
        
        periodos_dias_pendientes = {}
        for periodo in periodos_vacacionales:
            periodos_dias_pendientes[periodo.pk] = periodo.dias_pendientes_periodo
        context['periodos_dias_pendientes'] = json.dumps(periodos_dias_pendientes)
        
        if not context['tiene_periodos_vacacionales']:
            context['reintegros_pendientes'] = json.dumps([])
            context['tiene_reintegros_pendientes'] = False
            context['periodos_acumulados'] = None
            context['plazo_solicitud'] = None
            context['mostrar_alerta_periodos_acumulados'] = False
            context['periodos_dias_pendientes'] = json.dumps({})
            return context

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
        
        if context['tiene_reintegros_pendientes']:
            context['form'].initial['tiene_dias_pendientes'] = False

        context['puede_crear_solicitud'] = True
        context['solicitud_activa'] = None

        form = context.get('form')

        context['mostrar_alerta_periodos_acumulados'] = False
        
        if hasattr(form, 'periodos_acumulados') and form.periodos_acumulados:
            context['periodos_acumulados'] = form.periodos_acumulados
            context['periodo_mas_antiguo'] = form.periodo_mas_antiguo
            context['periodo_mas_reciente'] = form.periodo_mas_reciente
            context['periodo_mas_antiguo_habilitado'] = form.periodo_mas_antiguo_habilitado
            context['periodo_mas_reciente_habilitado'] = form.periodo_mas_reciente_habilitado

        context['plazo_solicitud'] = None
        
        return context

    def get_queryset(self):
        return SolicitudVacaciones.objects.filter(
            funcionario=self.request.user.funcionario
        )

    def dispatch(self, request, *args, **kwargs):
        solicitud = self.get_object()
        
        if not solicitud.puede_editar_eliminar:
            messages.error(request, "Solo puede editar solicitudes en estado 'pendiente' o 'devuelta' (no rechazadas por RRHH).")
            return redirect("vacaciones:solicitud-vacaciones-list")
        
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Solicitud actualizada correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        url = super().get_success_url()
        separador = '&' if ('?' in url) else '?'
        codigo = getattr(self.object, 'codigo_sabs', '') or ''
        codigo_q = urllib.parse.quote(codigo)
        return f"{url}{separador}actualizada=1&codigo={codigo_q}"

class SolicitudVacacionesDeleteView(LoginRequiredMixin, DeleteView):
    model = SolicitudVacaciones
    template_name = SOLICITUD_VACACIONES_CONFIRM_DELETE_TEMPLATE
    success_url = reverse_lazy("vacaciones:solicitud-vacaciones-list")

    def get_queryset(self):
        return SolicitudVacaciones.objects.filter(
            funcionario=self.request.user.funcionario
        )

    def dispatch(self, request, *args, **kwargs):
        solicitud = self.get_object()
        
        if not solicitud.puede_editar_eliminar:
            messages.error(request, "Solo puede eliminar solicitudes en estado 'pendiente' o 'devuelta' (no rechazadas por RRHH).")
            return redirect("vacaciones:solicitud-vacaciones-list")
        
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Solicitud eliminada correctamente.")
        return super().delete(request, *args, **kwargs)

def solicitud_vacaciones_create(request):
    years = [get_current_date_colombia().year, get_current_date_colombia().year + 1]
    festivos = []

    for y in years:
        festivos += [d.strftime('%d/%m/%Y') for d in holidays.Colombia(years=[y]).keys()]
        
    festivos_json = json.dumps(festivos)

    return render(request, SOLICITUD_VACACIONES_FORM_TEMPLATE, {'festivos_colombia': festivos_json})

# ==========================================================
# Parcial Semáforo
# ==========================================================
@login_required
def semaforo_cell(request, pk):
    sol = get_object_or_404(SolicitudVacaciones, pk=pk)

    if sol.aprobaciones.count() == 0:
        bulk = [
            AprobacionEtapa(solicitud=sol, etapa='JEFE', estado='pendiente'),
            AprobacionEtapa(solicitud=sol, etapa='COORD', estado='pendiente'),
            AprobacionEtapa(solicitud=sol, etapa='RRHH', estado='pendiente'),
        ]
        AprobacionEtapa.objects.bulk_create(bulk)

    return render(request, SEMAFORO_CELL_PARTIAL, {"solicitud": sol})

# ==========================================================
# Acciones de flujo (Funcionario/Jefe/Coord/RRHH)
# ==========================================================
@login_required
def aprobar_view(request, pk):
    sol = get_object_or_404(SolicitudVacaciones, pk=pk)
    try:
        aprobar_etapa(request.user, sol, observacion=request.POST.get('obs'))
        messages.success(request, "Etapa aprobada correctamente.")
    except (ValidationError, PermissionDenied) as e:
        messages.error(request, str(e))
    return redirect("vacaciones:solicitud-vacaciones-list")

@login_required
def devolver_view(request, pk):
    sol = get_object_or_404(SolicitudVacaciones, pk=pk)
    try:
        devolver_etapa(request.user, sol, observacion=request.POST.get('obs', ''))
        messages.info(request, "Solicitud devuelta al funcionario para ajustes.")
    except (ValidationError, PermissionDenied) as e:
        messages.error(request, str(e))
    return redirect("vacaciones:solicitud-vacaciones-list")

@login_required
def autorizar_view(request, pk):
    sol = get_object_or_404(SolicitudVacaciones, pk=pk)
    try:
        autorizar_rrhh(request.user, sol, observacion=request.POST.get('obs'))
        messages.success(request, "Solicitud autorizada por RRHH.")
    except (ValidationError, PermissionDenied) as e:
        messages.error(request, str(e))
    return redirect("vacaciones:solicitud-vacaciones-list")

@login_required
def rechazar_view(request, pk):
    sol = get_object_or_404(SolicitudVacaciones, pk=pk)
    try:
        rechazar_rrhh(request.user, sol, observacion=request.POST.get('obs', ''))
        messages.warning(request, "Solicitud rechazada por RRHH.")
    except (ValidationError, PermissionDenied) as e:
        messages.error(request, str(e))
    return redirect("vacaciones:solicitud-vacaciones-list")

@login_required
def reenviar_view(request, pk):
    sol = get_object_or_404(SolicitudVacaciones, pk=pk)
    try:
        reenviar_funcionario(request.user, sol, observacion=request.POST.get('obs'))
        messages.success(request, "Solicitud reenviada correctamente.")
    except (ValidationError, PermissionDenied) as e:
        messages.error(request, str(e))
    return redirect("vacaciones:solicitud-vacaciones-list")

# ==========================================================
# PDF - WeasyPrint
# ==========================================================
class SolicitudVacacionesPDFView(LoginRequiredMixin, View):
    """Genera el PDF de la solicitud con WeasyPrint."""

    def _split_fecha(self, f):
        if not f:
            return {"dia": "", "mes": "", "anio": ""}
        return {"dia": f.day, "mes": f.month, "anio": f.year}

    def _quincena(self, f):
        if not f:
            return {"q": "", "mes": "", "anio": ""}
        q = 1 if f.day <= 15 else 2
        return {"q": q, "mes": f.month, "anio": f.year}

    def get(self, request, pk):
        try:
            solicitud = SolicitudVacaciones.objects.select_related(
                "funcionario", "periodo_vacacional"
            ).prefetch_related(
                "aprobaciones__actualizado_por__funcionario"
            ).get(pk=pk)
        except SolicitudVacaciones.DoesNotExist:
            raise Http404("Solicitud no encontrada")

        owner_id = solicitud.funcionario_id
        user_funcionario_id = None
        es_jefe_del_funcionario = False
        es_secretaria_autorizada = False
        es_coordinador_autorizado = False
        es_rrhh_autorizado = False
        
        try:
            es_rrhh_autorizado = (
                es_rrhh(request.user) or 
                (hasattr(request.user, 'email') and request.user.email and "recursos.humanos" in request.user.email.lower())
            )
        except Exception:
            es_rrhh_autorizado = False
        
        if hasattr(request.user, "funcionario") and request.user.funcionario is not None:
            user_funcionario_id = request.user.funcionario.pk
            try:
                es_jefe_del_funcionario = (solicitud.funcionario.jefe_inmediato_id == request.user.funcionario.pk)
            except Exception:
                es_jefe_del_funcionario = False
            
            try:
                if es_secretaria(request.user):
                    secretaria_func = request.user.funcionario
                    if secretaria_func.jefe_inmediato and solicitud.funcionario.jefe_inmediato:
                        es_secretaria_autorizada = (secretaria_func.jefe_inmediato.pk == solicitud.funcionario.jefe_inmediato.pk)
            except Exception:
                es_secretaria_autorizada = False
            
            try:
                if es_coordinador_administrativo(request.user):
                    coord_func = request.user.funcionario
                    es_coordinador_autorizado = (coord_func.facultad_dependencia_id == solicitud.funcionario.facultad_dependencia_id)
            except Exception:
                es_coordinador_autorizado = False

        if not (
            request.user.is_staff
            or request.user.is_superuser
            or user_funcionario_id == owner_id
            or es_jefe_del_funcionario
            or es_secretaria_autorizada
            or es_coordinador_autorizado
            or es_rrhh_autorizado
        ):
            raise Http404("No autorizado")

        funcionario = solicitud.funcionario
        periodo = solicitud.periodo_vacacional

        # Fechas
        f_elab = self._split_fecha(solicitud.fecha_solicitud or date.today())
        f_inicio_periodo = self._split_fecha(getattr(periodo, "fecha_inicio_periodo", None))
        f_fin_periodo = self._split_fecha(getattr(periodo, "fecha_fin_periodo", None))
        f_inicio_disfrute = self._split_fecha(solicitud.fecha_inicio_vacaciones)
        f_fin_disfrute = self._split_fecha(solicitud.fecha_fin_vacaciones)
        f_pago = self._quincena(solicitud.fecha_pago)

        # Tipo de días
        estamento = funcionario.estamento.nombre.lower()
        decreto = (funcionario.decreto_resolucion or "").strip()
        es_habiles, es_calendario = False, False
        if estamento == "docente":
            if decreto == "1279":
                es_habiles, es_calendario = True, True
            elif decreto == "115":
                es_habiles, es_calendario = False, True
        elif estamento == "administrativo":
            es_habiles, es_calendario = True, False
        elif estamento == "trabajador oficial":
            es_habiles, es_calendario = False, True

        logo_url = request.build_absolute_uri(
            static("vacaciones/img/logosimbolo_univalle_negro.png")
        )

        # Obtener información de quien aprobó (Jefe Inmediato)
        aprobacion_jefe = solicitud.aprobaciones.filter(etapa='JEFE', estado='aprobada').first()
        autorizado_por = ""
        if aprobacion_jefe and aprobacion_jefe.actualizado_por:
            user_aprobador = aprobacion_jefe.actualizado_por
            if hasattr(user_aprobador, 'funcionario') and user_aprobador.funcionario:
                autorizado_por = f"{user_aprobador.funcionario.nombre} {user_aprobador.funcionario.apellido}"

        # Obtener información de quien aprobó (Coordinador Administrativo)
        aprobacion_coord = solicitud.aprobaciones.filter(etapa='COORD', estado='aprobada').first()
        coordinado_por = ""
        if aprobacion_coord and aprobacion_coord.actualizado_por:
            user_coordinador = aprobacion_coord.actualizado_por
            if hasattr(user_coordinador, 'funcionario') and user_coordinador.funcionario:
                coordinado_por = f"{user_coordinador.funcionario.nombre} {user_coordinador.funcionario.apellido}"

        # Obtener información de quien autorizó (RRHH)
        aprobacion_rrhh = solicitud.aprobaciones.filter(etapa='RRHH', estado='autorizada').first()
        autorizado_rrhh_por = ""
        if aprobacion_rrhh and aprobacion_rrhh.actualizado_por:
            user_rrhh = aprobacion_rrhh.actualizado_por
            if hasattr(user_rrhh, 'funcionario') and user_rrhh.funcionario:
                autorizado_rrhh_por = f"{user_rrhh.funcionario.nombre} {user_rrhh.funcionario.apellido}"
            else:
                autorizado_rrhh_por = f"{user_rrhh.get_full_name()}" if user_rrhh.get_full_name() else user_rrhh.email

        context = {
            "logo_url": logo_url,
            "pie_pagina": "F-01-MP-10-04-01 V-04-2014  |  Elaborado por: División de Recursos Humanos",

            "fecha_elaboracion": f_elab,
            "numero_identificacion": funcionario.numero_identificacion,
            "nombre_funcionario": f"{funcionario.nombre} {funcionario.apellido}",
            "estamento": funcionario.estamento.nombre,
            "facultad_dependencia": funcionario.facultad_dependencia.nombre,
            "codigo_sabs": solicitud.codigo_sabs,

            "periodo_desde": f_inicio_periodo,
            "periodo_hasta": f_fin_periodo,

            "dias_derecho": getattr(solicitud, "dias_derecho", None) or 30,
            "es_habiles": es_habiles,
            "es_calendario": es_calendario,

            "pago": f_pago,
            "disfrute_desde": f_inicio_disfrute,
            "disfrute_hasta": f_fin_disfrute,

            "observaciones": solicitud.observaciones or "",

            "solicitado_por": f"{funcionario.nombre} {funcionario.apellido}",
            "autorizado_por": autorizado_por,
            "coordinado_por": coordinado_por,
            "autorizado_rrhh_por": autorizado_rrhh_por,
        }

        html_string = render_to_string(SOLICITUD_VACACIONES_PDF_TEMPLATE, context)
        base_url = request.build_absolute_uri("/")
        pdf_bytes = HTML(string=html_string, base_url=base_url).write_pdf()

        file_stem = f"{solicitud.codigo_sabs}_{solicitud.funcionario.numero_identificacion}".replace(" ", "")
        filename = f"{file_stem}.pdf"

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'inline; filename="{filename}"; filename*=UTF-8\'\'{urllib.parse.quote(filename)}'
        )

        return response

# ==========================================================
# VISTA: Secretaria
# ==========================================================
@method_decorator(group_required("Secretaria"), name="dispatch")
class SecretariaSolicitudesListView(LoginRequiredMixin, ListView):
    """
    Lista las solicitudes de vacaciones que la secretaria puede ver:
    - De funcionarios que tienen el mismo jefe_inmediato que la secretaria
    - Incluye todas las solicitudes de los subordinados del jefe inmediato de la secretaria
    """
    model = SolicitudVacaciones
    template_name = SECRETARIA_SOLICITUDES_LIST_TEMPLATE
    context_object_name = "solicitudes"
    paginate_by = 20

    def get(self, request, *args, **kwargs):
        if request.htmx:
            self.object_list = self.get_queryset()
            context = self.get_context_data()
            html = render_to_string(TABLA_SECRETARIA_SOLICITUDES_PARTIAL, context, request)
            return HttpResponse(html)
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['solo_pdf'] = True
        return context

    def get_queryset(self):
        secretaria_func = getattr(self.request.user, "funcionario", None)
        
        if not secretaria_func or not secretaria_func.jefe_inmediato:
            return SolicitudVacaciones.objects.none()

        qs = (SolicitudVacaciones.objects
              .select_related("funcionario", "periodo_vacacional", "creada_por", "creada_por__funcionario")
              .filter(funcionario__jefe_inmediato=secretaria_func.jefe_inmediato)
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

@method_decorator(group_required("Secretaria"), name="dispatch")
class SecretariaSolicitudCreateView(LoginRequiredMixin, CreateView):
    """
    Permite a la secretaria crear solicitudes en nombre de funcionarios
    que cumplen los criterios de acceso.
    """
    model = SolicitudVacaciones
    form_class = SolicitudVacacionesForm
    template_name = SECRETARIA_SOLICITUD_FORM_TEMPLATE
    success_url = reverse_lazy("vacaciones:secretaria-solicitudes-list")

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
            return redirect("vacaciones:secretaria-solicitudes-list")
        
        secretaria_func = getattr(request.user, "funcionario", None)
        if not secretaria_func:
            messages.error(request, "No se encontró información del funcionario asociado.")
            return redirect("vacaciones:secretaria-solicitudes-list")
        
        try:
            funcionario_target = Funcionario.objects.get(pk=funcionario_id)
        except Funcionario.DoesNotExist:
            messages.error(request, "Funcionario no encontrado.")
            return redirect("vacaciones:secretaria-solicitudes-list")
        
        if not secretaria_func.jefe_inmediato or funcionario_target.jefe_inmediato != secretaria_func.jefe_inmediato:
            messages.error(request, "No tiene permisos para crear solicitudes para este funcionario.")
            return redirect("vacaciones:secretaria-solicitudes-list")
        
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
            return redirect("vacaciones:secretaria-solicitudes-list")
        
        periodos_vacacionales = PeriodoVacacional.objects.filter(funcionario=funcionario_target)
        if not periodos_vacacionales.exists():
            messages.error(
                request,
                "El funcionario seleccionado no tiene periodos vacacionales registrados y no puede crear una solicitud."
            )
            return redirect("vacaciones:secretaria-solicitudes-list")
        
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

        secretaria_func = getattr(request.user, "funcionario", None)
        if not secretaria_func:
            messages.error(request, "No se encontró información del funcionario asociado.")
            return self.form_invalid(self.get_form())

        if not secretaria_func.jefe_inmediato or funcionario_target.jefe_inmediato != secretaria_func.jefe_inmediato:
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

@method_decorator(group_required("Secretaria"), name="dispatch")
class SecretariaSolicitudUpdateView(LoginRequiredMixin, UpdateView):
    """
    Permite a la secretaria editar solicitudes SOLO si están en estado 'pendiente'.
    """
    model = SolicitudVacaciones
    form_class = SolicitudVacacionesForm
    template_name = SECRETARIA_SOLICITUD_FORM_TEMPLATE
    success_url = reverse_lazy("vacaciones:secretaria-solicitudes-list")

    def get_queryset(self):
        secretaria_func = getattr(self.request.user, "funcionario", None)
        
        if not secretaria_func:
            return SolicitudVacaciones.objects.none()

        if not secretaria_func.jefe_inmediato:
            return SolicitudVacaciones.objects.none()

        return SolicitudVacaciones.objects.filter(
            funcionario__jefe_inmediato=secretaria_func.jefe_inmediato
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['initial'] = kwargs.get('initial', {})
        if hasattr(self.get_object(), 'funcionario'):
            kwargs['initial']['user_id'] = self.get_object().funcionario.user.pk
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        solicitud = self.object
        
        hoy_colombia = get_current_date_colombia()
        years = [hoy_colombia.year, hoy_colombia.year + 1]
        festivos = []
        
        for y in years:
            festivos += [d.strftime('%d/%m/%Y') for d in holidays.Colombia(years=[y]).keys()]
        
        context['festivos_colombia'] = json.dumps(festivos)
        
        funcionario = solicitud.funcionario
        context['funcionario_target'] = funcionario
        context['funcionario_estamento'] = funcionario.estamento.nombre.lower()
        context['funcionario_decreto'] = (funcionario.decreto_resolucion or '').strip()
        
        periodos_vacacionales = PeriodoVacacional.objects.filter(funcionario=funcionario)
        context['tiene_periodos_vacacionales'] = True
        
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
        
        return context

    def dispatch(self, request, *args, **kwargs):
        solicitud = self.get_object()
        
        if not solicitud.puede_editar_eliminar:
            messages.error(request, "Solo puede editar solicitudes en estado 'pendiente' o 'devuelta' (no rechazadas por RRHH).")
            return redirect("vacaciones:secretaria-solicitudes-list")
        
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Solicitud actualizada correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        url = super().get_success_url()
        separador = '&' if ('?' in url) else '?'
        codigo = getattr(self.object, 'codigo_sabs', '') or ''
        codigo_q = urllib.parse.quote(codigo)
        return f"{url}{separador}actualizada=1&codigo={codigo_q}"

@method_decorator(group_required("Secretaria"), name="dispatch")
class SecretariaSolicitudDeleteView(LoginRequiredMixin, DeleteView):
    """
    Permite a la secretaria eliminar solicitudes SOLO si están en estado 'pendiente'.
    """
    model = SolicitudVacaciones
    template_name = SECRETARIA_SOLICIT_CONFIRM_DELETE_TEMPLATE
    success_url = reverse_lazy("vacaciones:secretaria-solicitudes-list")

    def get_queryset(self):
        secretaria_func = getattr(self.request.user, "funcionario", None)
        
        if not secretaria_func:
            return SolicitudVacaciones.objects.none()

        if not secretaria_func.jefe_inmediato:
            return SolicitudVacaciones.objects.none()

        return SolicitudVacaciones.objects.filter(
            funcionario__jefe_inmediato=secretaria_func.jefe_inmediato
        )

    def dispatch(self, request, *args, **kwargs):
        solicitud = self.get_object()
        
        if not solicitud.puede_editar_eliminar:
            messages.error(request, "Solo puede eliminar solicitudes en estado 'pendiente' o 'devuelta' (no rechazadas por RRHH).")
            return redirect("vacaciones:secretaria-solicitudes-list")
        
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Solicitud eliminada correctamente.")
        return super().delete(request, *args, **kwargs)
