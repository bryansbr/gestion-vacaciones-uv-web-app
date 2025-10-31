from datetime import date
import json
import urllib.parse

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.timezone import localdate, now
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
import holidays
from weasyprint import HTML

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

# -----------------------------------------
# VISTA: PeriodoVacacional
# -----------------------------------------
class PeriodoVacacionalListView(LoginRequiredMixin, ListView):
    model = PeriodoVacacional
    template_name = "vacaciones/periodo-vacacional-list.html"
    context_object_name = "periodos"

class PeriodoVacacionalCreateView(LoginRequiredMixin, CreateView):
    model = PeriodoVacacional
    form_class = PeriodoVacacionalForm
    template_name = "vacaciones/periodo-vacacional-form.html"
    success_url = reverse_lazy("vacaciones:periodo-vacacional-list")

    def form_valid(self, form):
        messages.success(self.request, "Periodo vacacional creado correctamente.")
        return super().form_valid(form)

class PeriodoVacacionalUpdateView(LoginRequiredMixin, UpdateView):
    model = PeriodoVacacional
    form_class = PeriodoVacacionalForm
    template_name = "vacaciones/periodo-vacacional-form.html"
    success_url = reverse_lazy("vacaciones:periodo-vacacional-list")

    def form_valid(self, form):
        messages.success(self.request, "Periodo vacacional actualizado correctamente.")
        return super().form_valid(form)

class PeriodoVacacionalDeleteView(LoginRequiredMixin, DeleteView):
    model = PeriodoVacacional
    template_name = "vacaciones/periodo-vacacional-confirm-delete.html"
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
    template_name = "vacaciones/solicitud-vacaciones-form.html"
    success_url = reverse_lazy("vacaciones:solicitud-vacaciones-list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
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

        # Verificar si el funcionario tiene periodos vacacionales
        periodos_vacacionales = PeriodoVacacional.objects.filter(funcionario=funcionario)
        context['tiene_periodos_vacacionales'] = periodos_vacacionales.exists()
        
        periodos_dias_pendientes = {}
        for periodo in periodos_vacacionales:
            periodos_dias_pendientes[periodo.pk] = periodo.dias_pendientes_periodo
        context['periodos_dias_pendientes'] = json.dumps(periodos_dias_pendientes)
        
        # Verificar si puede solicitar vacaciones según los nuevos plazos límite
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

        # Reintegros aprobados con días pendientes
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
        
        # Inicializar el campo tiene_dias_pendientes si hay reintegros pendientes
        if context['tiene_reintegros_pendientes']:
            context['form'].initial['tiene_dias_pendientes'] = False

        # Verificar si el funcionario tiene una solicitud activa (sin reintegro asociado)
        solicitudes_activas = SolicitudVacaciones.objects.filter(
            funcionario=funcionario,
            estado_solicitud__in=['pendiente', 'en_revision', 'aprobado']
        ).prefetch_related('reintegrovacaciones_set')
        
        # Una solicitud se considera "culminada" si tiene un reintegro asociado
        solicitudes_sin_reintegro = []
        for solicitud in solicitudes_activas:
            tiene_reintegro = any(
                reintegro.estado_solicitud == 'aprobado' 
                for reintegro in solicitud.reintegrovacaciones_set.all()
            )
            
            if not tiene_reintegro:
                solicitudes_sin_reintegro.append(solicitud)
        
        # Solo verificar solicitudes activas, NO plazos límite para el botón Crear
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
                    periodo_vacacional__in=[form.periodo_mas_antiguo, form.periodo_mas_reciente]
                ).exists()
                context['mostrar_alerta_periodos_acumulados'] = not solicitudes_periodos_acumulados

        context['plazo_solicitud'] = mensaje_plazo
        
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
    template_name = "vacaciones/solicitud-vacaciones-list.html"
    context_object_name = "solicitudes"

    def get_queryset(self):
        return SolicitudVacaciones.objects.filter(funcionario=self.request.user.funcionario).order_by('-fecha_solicitud')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        funcionario = self.request.user.funcionario
        
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
        
        puede_solicitar_hoy, mensaje_plazo = puede_solicitar_vacaciones_hoy(
            funcionario.estamento.nombre.lower(),
            funcionario.decreto_resolucion
        )
        
        context['puede_crear_solicitud'] = len(solicitudes_sin_reintegro) == 0
        context['solicitud_activa'] = solicitudes_sin_reintegro[0] if solicitudes_sin_reintegro else None
        context['mensaje_plazo'] = None
        
        context['tiene_periodos'] = PeriodoVacacional.objects.filter(funcionario=funcionario).exists()
        
        return context

class SolicitudVacacionesUpdateView(LoginRequiredMixin, UpdateView):
    model = SolicitudVacaciones
    form_class = SolicitudVacacionesForm
    template_name = "vacaciones/solicitud-vacaciones-form.html"
    success_url = reverse_lazy("vacaciones:solicitud-vacaciones-list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
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
            funcionario=self.request.user.funcionario,
            estado_solicitud='pendiente'
        )

    def form_valid(self, form):
        messages.success(self.request, "Solicitud actualizada correctamente.")
        return super().form_valid(form)

class SolicitudVacacionesDeleteView(LoginRequiredMixin, DeleteView):
    model = SolicitudVacaciones
    template_name = "vacaciones/solicitud-vacaciones-confirm-delete.html"
    success_url = reverse_lazy("vacaciones:solicitud-vacaciones-list")

    def get_queryset(self):
        return SolicitudVacaciones.objects.filter(
            funcionario=self.request.user.funcionario,
            estado_solicitud='pendiente'
        )

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Solicitud eliminada correctamente.")
        return super().delete(request, *args, **kwargs)

def solicitud_vacaciones_create(request):
    years = [get_current_date_colombia().year, get_current_date_colombia().year + 1]
    festivos = []

    for y in years:
        festivos += [d.strftime('%d/%m/%Y') for d in holidays.Colombia(years=[y]).keys()]
        
    festivos_json = json.dumps(festivos)

    return render(request, 'vacaciones/solicitud-vacaciones-form.html', {'festivos_colombia': festivos_json})

# ==========================================================
# Parcial Semáforo (corregida la ruta del template)
# ==========================================================

@login_required
def semaforo_cell(request, pk):
    sol = get_object_or_404(SolicitudVacaciones, pk=pk)

    # Backfill si la solicitud no tiene etapas (p. ej. solicitudes viejas)
    if sol.aprobaciones.count() == 0:
        bulk = [
            AprobacionEtapa(solicitud=sol, etapa='JEFE', estado='pendiente'),
            AprobacionEtapa(solicitud=sol, etapa='COORD', estado='pendiente'),
            AprobacionEtapa(solicitud=sol, etapa='RRHH', estado='pendiente'),
        ]
        AprobacionEtapa.objects.bulk_create(bulk)

    return render(request, "vacaciones/partials/_semaforo-cell.html", {"solicitud": sol})

# ==========================================================
# Acciones de flujo (JEFE/COORD/RRHH/Funcionario)
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
            ).get(pk=pk)
        except SolicitudVacaciones.DoesNotExist:
            raise Http404("Solicitud no encontrada")

        # -------- AUTORIZACIÓN --------
        owner_id = solicitud.funcionario_id
        user_funcionario_id = None
        es_jefe_del_funcionario = False
        if hasattr(request.user, "funcionario") and request.user.funcionario is not None:
            user_funcionario_id = request.user.funcionario.pk
            try:
                es_jefe_del_funcionario = (solicitud.funcionario.jefe_inmediato_id == request.user.funcionario.pk)
            except Exception:
                es_jefe_del_funcionario = False

        if not (
            request.user.is_staff
            or request.user.is_superuser
            or user_funcionario_id == owner_id
            or es_jefe_del_funcionario
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
        }

        html_string = render_to_string("vacaciones/pdf/solicitud-vacaciones.html", context)
        base_url = request.build_absolute_uri("/")  # resuelve static/imagenes
        pdf_bytes = HTML(string=html_string, base_url=base_url).write_pdf()

        file_stem = f"{solicitud.codigo_sabs}_{solicitud.funcionario.numero_identificacion}".replace(" ", "")
        filename = f"{file_stem}.pdf"

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'inline; filename="{filename}"; filename*=UTF-8\'\'{urllib.parse.quote(filename)}'
        )

        return response
