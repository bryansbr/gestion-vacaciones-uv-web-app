from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic import ListView

from core.permissions import es_rrhh
from .models import SolicitudVacaciones, ReintegroVacaciones
from .services.aprobaciones import (
    autorizar_rrhh,
    rechazar_rrhh,
)
from .services.reintegros import (
    autorizar_rrhh_reintegro,
    rechazar_rrhh_reintegro,
)

# ==========================================================
# CONSTANTES
# ==========================================================
RRHH_SOLICITUDES_TEMPLATE = "vacaciones/roles/rrhh/rrhh-solicitudes-list.html"
RRHH_SOLICITUDES_TABLE_PARTIAL = "vacaciones/partials/_tabla-rrhh-solicitudes.html"
RRHH_REINTEGROS_TEMPLATE = "vacaciones/roles/rrhh/rrhh-reintegros-list.html"
RRHH_REINTEGROS_TABLE_PARTIAL = "vacaciones/partials/_tabla-reintegros.html"

def _es_rrhh_o_email(user):
    """
    Verifica si el usuario es RRHH o tiene email de RRHH (temporal hasta asignar grupo).
    """
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if es_rrhh(user):
        return True
    if hasattr(user, 'email') and user.email and "recursos.humanos" in user.email.lower():
        return True
    return False

class SolicitudesRRHHListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Lista todas las solicitudes de vacaciones que RRHH puede ver:
    - De todos los funcionarios de la Universidad (sin restricción por Facultad o Dependencia)
    - Solo aquellas que han sido aprobadas por el Coordinador Administrativo (etapa COORD aprobada)
    """
    model = SolicitudVacaciones
    template_name = RRHH_SOLICITUDES_TEMPLATE
    context_object_name = "solicitudes"
    raise_exception = False
    
    def test_func(self):
        """Verifica si el usuario tiene permiso para acceder."""
        return _es_rrhh_o_email(self.request.user)
    
    def handle_no_permission(self):
        """Maneja el caso cuando el usuario no tiene permisos."""
        messages.error(self.request, "No tiene permisos para acceder a esta sección.")
        return redirect('usuarios:dashboard')

    def get(self, request, *args, **kwargs):
        if request.htmx:
            self.object_list = self.get_queryset()
            context = self.get_context_data()
            html = render_to_string(RRHH_SOLICITUDES_TABLE_PARTIAL, context, request)
            return HttpResponse(html)
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """
        RRHH puede ver todas las solicitudes que:
        1. Han pasado por el flujo completo (JEFE y COORD aprobadas)
        2. O las que RRHH haya procesado anteriormente (autorizadas o rechazadas)
        """
        from django.db.models import Count
        
        ids_jefe_aprobada = set(
            SolicitudVacaciones.objects
            .filter(aprobaciones__etapa='JEFE', aprobaciones__estado='aprobada')
            .values_list('id', flat=True)
            .distinct()
        )
        
        ids_coord_aprobada = set(
            SolicitudVacaciones.objects
            .filter(aprobaciones__etapa='COORD', aprobaciones__estado='aprobada')
            .values_list('id', flat=True)
            .distinct()
        )
        
        ids_jefe_y_coord = ids_jefe_aprobada & ids_coord_aprobada
        
        ids_rrhh_procesadas = set(
            SolicitudVacaciones.objects
            .filter(aprobaciones__etapa='RRHH', aprobaciones__estado__in=['autorizada', 'rechazada'])
            .values_list('id', flat=True)
            .distinct()
        )
        
        ids_combinados = ids_jefe_y_coord | ids_rrhh_procesadas
        
        if not ids_combinados:
            return SolicitudVacaciones.objects.none()
        
        qs_final = (SolicitudVacaciones.objects
                   .select_related("funcionario", "periodo_vacacional", "creada_por", "creada_por__funcionario")
                   .prefetch_related("aprobaciones")
                   .filter(id__in=ids_combinados)
                   .distinct()
                   .order_by("-fecha_solicitud", "-id"))


        return qs_final

def solicitud_pdf(request, pk):
    """Permite a RRHH ver el PDF de cualquier solicitud."""
    if not _es_rrhh_o_email(request.user):
        return HttpResponseForbidden("No tiene permisos para acceder a esta solicitud.")
    solicitud = get_object_or_404(SolicitudVacaciones, pk=pk)
    return redirect(solicitud.pdf_url)

def autorizar_solicitud(request, pk):
    """Autoriza una solicitud de vacaciones."""
    if not _es_rrhh_o_email(request.user):
        return HttpResponseForbidden("No tiene permisos para autorizar solicitudes.")
    
    if request.method != "POST":
        return HttpResponseBadRequest("Método no permitido")
    
    solicitud = get_object_or_404(SolicitudVacaciones, pk=pk)
    
    try:
        autorizar_rrhh(request.user, solicitud, observacion=request.POST.get('obs', ''))
        messages.success(request, "Solicitud autorizada correctamente. El funcionario saldrá a vacaciones y se realizará el pago correspondiente.")
    except (ValidationError, PermissionDenied) as e:
        messages.error(request, str(e))
    
    return redirect(reverse("vacaciones:rrhh_solicitudes_list"))

def rechazar_solicitud(request, pk):
    """Rechaza una solicitud de vacaciones."""
    if not _es_rrhh_o_email(request.user):
        return HttpResponseForbidden("No tiene permisos para rechazar solicitudes.")
    
    if request.method != "POST":
        return HttpResponseBadRequest("Método no permitido")
    
    solicitud = get_object_or_404(SolicitudVacaciones, pk=pk)
    
    try:
        rechazar_rrhh(request.user, solicitud, observacion=request.POST.get('obs', ''))
        messages.warning(request, "La solicitud fue rechazada. Se notificó al funcionario, C.A. y Jefe Inmediato.")
    except (ValidationError, PermissionDenied) as e:
        messages.error(request, str(e))
    
    return redirect(reverse("vacaciones:rrhh_solicitudes_list"))

class ReintegrosRRHHListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Lista todas las solicitudes de reintegro de vacaciones que RRHH puede ver:
    - De todos los funcionarios de la Universidad (sin restricción por Facultad o Dependencia)
    - Solo aquellas que han sido aprobadas por el Coordinador Administrativo (etapa COORD aprobada)
    """
    model = ReintegroVacaciones
    template_name = RRHH_REINTEGROS_TEMPLATE
    context_object_name = "reintegros"
    raise_exception = False
    
    def test_func(self):
        """Verifica si el usuario tiene permiso para acceder."""
        return _es_rrhh_o_email(self.request.user)
    
    def handle_no_permission(self):
        """Maneja el caso cuando el usuario no tiene permisos."""
        messages.error(self.request, "No tiene permisos para acceder a esta sección.")
        return redirect('usuarios:dashboard')

    def get(self, request, *args, **kwargs):
        if request.htmx:
            self.object_list = self.get_queryset()
            context = self.get_context_data()
            context['tabla_id'] = 'tabla-reintegros-rrhh'
            html = render_to_string(RRHH_REINTEGROS_TABLE_PARTIAL, context, request)
            return HttpResponse(html)
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """
        RRHH puede ver todas las solicitudes de reintegro que:
        1. Han pasado por el flujo completo (JEFE y COORD aprobadas)
        2. O las que RRHH haya procesado anteriormente (autorizadas o rechazadas)
        """
        ids_jefe_aprobada = set(
            ReintegroVacaciones.objects
            .filter(aprobaciones__etapa='JEFE', aprobaciones__estado='aprobada')
            .values_list('id', flat=True)
            .distinct()
        )
        
        ids_coord_aprobada = set(
            ReintegroVacaciones.objects
            .filter(aprobaciones__etapa='COORD', aprobaciones__estado='aprobada')
            .values_list('id', flat=True)
            .distinct()
        )
        
        ids_jefe_y_coord = ids_jefe_aprobada & ids_coord_aprobada
        
        ids_rrhh_procesadas = set(
            ReintegroVacaciones.objects
            .filter(aprobaciones__etapa='RRHH', aprobaciones__estado__in=['autorizada', 'rechazada'])
            .values_list('id', flat=True)
            .distinct()
        )
        
        ids_combinados = ids_jefe_y_coord | ids_rrhh_procesadas
        
        if not ids_combinados:
            return ReintegroVacaciones.objects.none()
        
        qs_final = (ReintegroVacaciones.objects
                   .select_related("funcionario", "funcionario__facultad_dependencia", "creada_por", "creada_por__funcionario", "solicitud_vacaciones", "periodo_vacacional")
                   .prefetch_related("aprobaciones")
                   .filter(id__in=ids_combinados)
                   .distinct()
                   .order_by("-fecha_solicitud", "-id"))

        return qs_final

def autorizar_reintegro(request, pk):
    """Autoriza un reintegro de vacaciones."""
    if not _es_rrhh_o_email(request.user):
        return HttpResponseForbidden("No tiene permisos para autorizar reintegros.")
    
    if request.method != "POST":
        return HttpResponseBadRequest("Método no permitido")
    
    reintegro = get_object_or_404(ReintegroVacaciones, pk=pk)
    
    try:
        autorizar_rrhh_reintegro(request.user, reintegro, observacion=request.POST.get('obs', ''))
        messages.success(request, "Reintegro autorizado correctamente. El funcionario queda oficialmente reincorporado a sus labores.")
    except (ValidationError, PermissionDenied) as e:
        messages.error(request, str(e))
    
    return redirect(reverse("vacaciones:rrhh_reintegros_list"))

def rechazar_reintegro(request, pk):
    """Rechaza un reintegro de vacaciones."""
    if not _es_rrhh_o_email(request.user):
        return HttpResponseForbidden("No tiene permisos para rechazar reintegros.")
    
    if request.method != "POST":
        return HttpResponseBadRequest("Método no permitido")
    
    reintegro = get_object_or_404(ReintegroVacaciones, pk=pk)
    
    try:
        rechazar_rrhh_reintegro(request.user, reintegro, observacion=request.POST.get('obs', ''))
        messages.warning(request, "El reintegro fue rechazado. Se notificó al funcionario, C.A. y Jefe Inmediato.")
    except (ValidationError, PermissionDenied) as e:
        messages.error(request, str(e))
    
    return redirect(reverse("vacaciones:rrhh_reintegros_list"))
