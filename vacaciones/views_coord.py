from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
import json

from core.permissions import group_required
from usuarios.models import Funcionario
from .models import SolicitudVacaciones, ReintegroVacaciones, generar_codigo_sabs
from .services.aprobaciones import aprobar_etapa, devolver_etapa
from .services.reintegros import aprobar_etapa_reintegro, devolver_etapa_reintegro
from .forms import ReintegroVacacionesForm
from .utils import get_current_date_colombia
from .views import ReintegroVacacionesListView

# ==========================================================
# CONSTANTES
# ==========================================================
COORD_SOLICITUDES_TEMPLATE = "vacaciones/roles/coord/coord-solicitudes-list.html"
COORD_SOLICITUDES_TABLE_PARTIAL = "vacaciones/partials/_tabla-coord-solicitudes.html"
COORD_REINTEGROS_TEMPLATE = "vacaciones/roles/coord/coord-reintegros-list.html"
COORD_REINTEGROS_TABLE_PARTIAL = "vacaciones/partials/_tabla-coord-reintegros.html"
COORD_REINTEGRO_FORM_TEMPLATE = "vacaciones/roles/coord/coord-reintegro-form.html"
COORD_REINTEGRO_CONFIRM_DELETE_TEMPLATE = "vacaciones/roles/coord/coord-reintegro-confirm-delete.html"

def _es_coordinador_de_facultad(solicitud, user):
    """
    Verifica si el usuario es Coordinador Administrativo de la misma 
    facultad/dependencia que el funcionario de la solicitud.
    """
    user_func = getattr(user, "funcionario", None)
    if not user_func:
        return False
    return solicitud.funcionario.facultad_dependencia_id == user_func.facultad_dependencia_id

def _es_coordinador_de_facultad_reintegro(reintegro, user):
    """
    Verifica si el usuario es Coordinador Administrativo de la misma 
    facultad/dependencia que el funcionario del reintegro.
    """
    user_func = getattr(user, "funcionario", None)
    if not user_func:
        return False
    return reintegro.funcionario.facultad_dependencia_id == user_func.facultad_dependencia_id

@method_decorator(group_required("Coordinador Administrativo"), name="dispatch")
class SolicitudesCoordListView(LoginRequiredMixin, ListView):
    """
    Lista las solicitudes de vacaciones que el Coordinador Administrativo puede ver:
    - De funcionarios que pertenecen a la misma facultad_dependencia
    - Solo aquellas que han sido aprobadas por el Jefe Inmediato (etapa JEFE aprobada)
    """
    model = SolicitudVacaciones
    template_name = COORD_SOLICITUDES_TEMPLATE
    context_object_name = "solicitudes"
    paginate_by = 20

    def get(self, request, *args, **kwargs):
        if request.htmx:
            self.object_list = self.get_queryset()
            context = self.get_context_data()
            html = render_to_string(COORD_SOLICITUDES_TABLE_PARTIAL, context, request)
            return HttpResponse(html)
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        coord_func = getattr(self.request.user, "funcionario", None)

        if not coord_func:
            return SolicitudVacaciones.objects.none()

        qs = (SolicitudVacaciones.objects
              .select_related("funcionario", "periodo_vacacional", "creada_por", "creada_por__funcionario")
              .prefetch_related("aprobaciones")
              .filter(
                  funcionario__facultad_dependencia=coord_func.facultad_dependencia,
                  aprobaciones__etapa='JEFE',
                  aprobaciones__estado='aprobada'
              )
              .distinct()
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
        context["rol_actual"] = "coordinador_administrativo"
        context["mostrar_alerta_rol"] = user.groups.filter(name="Jefe Inmediato").exists()
        context["etiqueta_rol_actual"] = "Coordinación Administrativa"
        return context

def solicitud_pdf(request, pk):
    solicitud = get_object_or_404(SolicitudVacaciones, pk=pk)
    if not _es_coordinador_de_facultad(solicitud, request.user) and not request.user.is_superuser:
        return HttpResponseForbidden()
    return redirect(solicitud.pdf_url)

@group_required("Coordinador Administrativo")
def aprobar_solicitud(request, pk):
    if request.method != "POST":
        return HttpResponseBadRequest("Método no permitido")
    solicitud = get_object_or_404(SolicitudVacaciones, pk=pk)
    if not _es_coordinador_de_facultad(solicitud, request.user) and not request.user.is_superuser:
        return HttpResponseForbidden()

    try:
        aprobar_etapa(request.user, solicitud, observacion=request.POST.get('obs', ''))
        messages.success(request, "Solicitud aprobada correctamente. Se ha enviado a Recursos Humanos.")
    except (ValidationError, PermissionDenied) as e:
        messages.error(request, str(e))
    
    return redirect(reverse("vacaciones:coord_solicitudes_list"))

@group_required("Coordinador Administrativo")
def devolver_solicitud(request, pk):
    if request.method != "POST":
        return HttpResponseBadRequest("Método no permitido")
    solicitud = get_object_or_404(SolicitudVacaciones, pk=pk)
    if not _es_coordinador_de_facultad(solicitud, request.user) and not request.user.is_superuser:
        return HttpResponseForbidden()

    try:
        devolver_etapa(request.user, solicitud, observacion=request.POST.get('obs', ''))
        messages.info(request, "La solicitud fue devuelta al funcionario con observaciones.")
    except (ValidationError, PermissionDenied) as e:
        messages.error(request, str(e))
    
    return redirect(reverse("vacaciones:coord_solicitudes_list"))

@method_decorator(group_required("Coordinador Administrativo"), name="dispatch")
class ReintegrosCoordListView(LoginRequiredMixin, ListView):
    """
    Lista los reintegros de vacaciones que el Coordinador Administrativo puede ver:
    - De funcionarios que pertenecen a la misma facultad_dependencia
    - Solo aquellos que han sido aprobados por el Jefe Inmediato (etapa JEFE aprobada)
    """
    model = ReintegroVacaciones
    template_name = COORD_REINTEGROS_TEMPLATE
    context_object_name = "reintegros"
    paginate_by = 20

    def get(self, request, *args, **kwargs):
        if request.htmx:
            self.object_list = self.get_queryset()
            context = self.get_context_data()
            html = render_to_string(COORD_REINTEGROS_TABLE_PARTIAL, context, request)
            return HttpResponse(html)
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        coord_func = getattr(self.request.user, "funcionario", None)

        if not coord_func:
            return ReintegroVacaciones.objects.none()

        qs = (ReintegroVacaciones.objects
              .select_related("funcionario", "funcionario__facultad_dependencia", "creada_por", "creada_por__funcionario", "solicitud_vacaciones", "periodo_vacacional")
              .prefetch_related("aprobaciones")
              .filter(
                  funcionario__facultad_dependencia=coord_func.facultad_dependencia,
                  aprobaciones__etapa='JEFE',
                  aprobaciones__estado='aprobada'
              )
              .distinct()
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
        context["rol_actual"] = "coordinador_administrativo"
        context["mostrar_alerta_rol"] = user.groups.filter(name="Jefe Inmediato").exists()
        context["etiqueta_rol_actual"] = "Coordinación Administrativa"
        
        coord_func = getattr(self.request.user, "funcionario", None)
        if coord_func:
            funcionarios_facultad = Funcionario.objects.filter(
                facultad_dependencia=coord_func.facultad_dependencia
            ).select_related('facultad_dependencia')
            
            funcionarios_data = []
            
            solicitudes_coord = ReintegroVacacionesListView._solicitudes_autorizadas_sin_reintegro(coord_func)
            funcionarios_data.append({
                'id': coord_func.pk,
                'nombre': coord_func.nombre,
                'apellido': coord_func.apellido,
                'facultad_dependencia': coord_func.facultad_dependencia.nombre if coord_func.facultad_dependencia else '',
                'tiene_solicitudes_autorizadas': len(solicitudes_coord) > 0,
                'solicitudes_autorizadas': [
                    {
                        'id': sol.pk,
                        'codigo_sabs': sol.codigo_sabs,
                        'fecha_inicio': sol.fecha_inicio_vacaciones.strftime('%d/%m/%Y'),
                        'fecha_fin': sol.fecha_fin_vacaciones.strftime('%d/%m/%Y')
                    }
                    for sol in solicitudes_coord
                ]
            })
            
            for func in funcionarios_facultad.exclude(pk=coord_func.pk):
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
            
            context["funcionarios_bajo_coord"] = json.dumps(funcionarios_data)
        else:
            context["funcionarios_bajo_coord"] = json.dumps([])

        return context

@group_required("Coordinador Administrativo")
def aprobar_reintegro(request, pk):
    if request.method != "POST":
        return HttpResponseBadRequest("Método no permitido")
    reintegro = get_object_or_404(ReintegroVacaciones, pk=pk)
    if not _es_coordinador_de_facultad_reintegro(reintegro, request.user) and not request.user.is_superuser:
        return HttpResponseForbidden()

    try:
        aprobar_etapa_reintegro(request.user, reintegro, observacion=request.POST.get('obs', ''))
        messages.success(request, "Reintegro aprobado correctamente. Se ha enviado a Recursos Humanos.")
    except (ValidationError, PermissionDenied) as e:
        messages.error(request, str(e))
    
    return redirect(reverse("vacaciones:coord_reintegros_list"))

@group_required("Coordinador Administrativo")
def devolver_reintegro(request, pk):
    if request.method != "POST":
        return HttpResponseBadRequest("Método no permitido")
    reintegro = get_object_or_404(ReintegroVacaciones, pk=pk)
    if not _es_coordinador_de_facultad_reintegro(reintegro, request.user) and not request.user.is_superuser:
        return HttpResponseForbidden()

    try:
        devolver_etapa_reintegro(request.user, reintegro, observacion=request.POST.get('obs', ''))
        messages.info(request, "El reintegro fue devuelto al funcionario con observaciones.")
    except (ValidationError, PermissionDenied) as e:
        messages.error(request, str(e))
    
    return redirect(reverse("vacaciones:coord_reintegros_list"))

@method_decorator(group_required("Coordinador Administrativo"), name="dispatch")
class CoordReintegroCreateView(LoginRequiredMixin, CreateView):
    """
    Permite al coordinador crear reintegros en nombre de funcionarios
    que pertenecen a su misma facultad/dependencia.
    """
    model = ReintegroVacaciones
    form_class = ReintegroVacacionesForm
    template_name = COORD_REINTEGRO_FORM_TEMPLATE
    success_url = reverse_lazy("vacaciones:coord_reintegros_list")

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
        coord_func = getattr(request.user, "funcionario", None)
        if not coord_func:
            messages.error(request, "No se encontró información del funcionario asociado.")
            return redirect("vacaciones:coord_reintegros_list")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        coord_func = getattr(self.request.user, "funcionario", None)
        
        if coord_func:
            funcionarios_facultad = Funcionario.objects.filter(
                facultad_dependencia=coord_func.facultad_dependencia
            ).select_related('facultad_dependencia')
            
            funcionarios_data = []
            
            solicitudes_coord = ReintegroVacacionesListView._solicitudes_autorizadas_sin_reintegro(coord_func)
            funcionarios_data.append({
                'id': coord_func.pk,
                'nombre': coord_func.nombre,
                'apellido': coord_func.apellido,
                'facultad_dependencia': coord_func.facultad_dependencia.nombre if coord_func.facultad_dependencia else '',
                'tiene_solicitudes_autorizadas': len(solicitudes_coord) > 0,
                'solicitudes_autorizadas': [
                    {
                        'id': sol.pk,
                        'codigo_sabs': sol.codigo_sabs,
                        'fecha_inicio': sol.fecha_inicio_vacaciones.strftime('%d/%m/%Y'),
                        'fecha_fin': sol.fecha_fin_vacaciones.strftime('%d/%m/%Y')
                    }
                    for sol in solicitudes_coord
                ]
            })
            
            for func in funcionarios_facultad.exclude(pk=coord_func.pk):
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
            
            context["funcionarios_bajo_coord"] = json.dumps(funcionarios_data)
        else:
            context["funcionarios_bajo_coord"] = json.dumps([])

        context["etiqueta_rol_actual"] = "Coordinación Administrativa"
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

        coord_func = getattr(request.user, "funcionario", None)
        if not coord_func:
            messages.error(request, "No se encontró información del funcionario asociado.")
            return self.form_invalid(self.get_form())

        if funcionario_target.facultad_dependencia != coord_func.facultad_dependencia:
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

@method_decorator(group_required("Coordinador Administrativo"), name="dispatch")
class CoordReintegroUpdateView(LoginRequiredMixin, UpdateView):
    """
    Permite al coordinador editar reintegros SOLO si están en estado 'pendiente' o 'devuelta'
    y pertenecen a funcionarios de su facultad/dependencia.
    """
    model = ReintegroVacaciones
    form_class = ReintegroVacacionesForm
    template_name = COORD_REINTEGRO_FORM_TEMPLATE
    success_url = reverse_lazy("vacaciones:coord_reintegros_list")

    def get_queryset(self):
        coord_func = getattr(self.request.user, "funcionario", None)
        
        if not coord_func:
            return ReintegroVacaciones.objects.none()

        return ReintegroVacaciones.objects.filter(
            funcionario__facultad_dependencia=coord_func.facultad_dependencia
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        
        reintegro = self.get_object()
        if reintegro and reintegro.funcionario:
            kwargs['funcionario_id'] = reintegro.funcionario.pk
        
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reintegro = self.get_object()
        
        coord_func = getattr(self.request.user, "funcionario", None)
        if coord_func:
            funcionarios_facultad = Funcionario.objects.filter(
                facultad_dependencia=coord_func.facultad_dependencia
            ).select_related('facultad_dependencia')
            
            funcionarios_data = []
            
            from .views import ReintegroVacacionesListView
            for func in funcionarios_facultad:
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
            
            context["funcionarios_bajo_coord"] = json.dumps(funcionarios_data)
        else:
            context["funcionarios_bajo_coord"] = json.dumps([])

        context["etiqueta_rol_actual"] = "Coordinación Administrativa"
        return context

    def dispatch(self, request, *args, **kwargs):
        reintegro = self.get_object()
        
        if not reintegro.puede_editar_eliminar:
            messages.error(request, "Solo puede editar reintegros en estado 'pendiente' o 'devuelta'.")
            return redirect("vacaciones:coord_reintegros_list")
        
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        import urllib.parse
        reintegro = form.save()
        codigo = reintegro.codigo_sabs
        messages.success(self.request, "Reintegro actualizado correctamente.")
        url = self.get_success_url()
        separador = '&' if ('?' in url) else '?'
        codigo_q = urllib.parse.quote(codigo)
        return redirect(f"{url}{separador}actualizado=1&codigo={codigo_q}")

@method_decorator(group_required("Coordinador Administrativo"), name="dispatch")
class CoordReintegroDeleteView(LoginRequiredMixin, DeleteView):
    """
    Permite al coordinador eliminar reintegros SOLO si están en estado 'pendiente' o 'devuelta'
    y pertenecen a funcionarios de su facultad/dependencia.
    """
    model = ReintegroVacaciones
    template_name = COORD_REINTEGRO_CONFIRM_DELETE_TEMPLATE
    success_url = reverse_lazy("vacaciones:coord_reintegros_list")

    def get_queryset(self):
        coord_func = getattr(self.request.user, "funcionario", None)
        
        if not coord_func:
            return ReintegroVacaciones.objects.none()

        return ReintegroVacaciones.objects.filter(
            funcionario__facultad_dependencia=coord_func.facultad_dependencia
        )

    def dispatch(self, request, *args, **kwargs):
        reintegro = self.get_object()
        
        if not reintegro.puede_editar_eliminar:
            messages.error(request, "Solo puede eliminar reintegros en estado 'pendiente' o 'devuelta'.")
            return redirect("vacaciones:coord_reintegros_list")
        
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        import urllib.parse
        reintegro = self.get_object()
        codigo = reintegro.codigo_sabs
        messages.success(request, "Reintegro eliminado correctamente.")
        response = super().delete(request, *args, **kwargs)
        url = self.get_success_url()
        separador = '&' if ('?' in url) else '?'
        codigo_q = urllib.parse.quote(codigo)
        return redirect(f"{url}{separador}eliminado=1&codigo={codigo_q}")
