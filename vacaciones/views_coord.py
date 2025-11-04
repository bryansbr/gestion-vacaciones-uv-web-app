import holidays
import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import ListView

from core.permissions import group_required
from usuarios.models import Funcionario
from .models import SolicitudVacaciones
from .services.aprobaciones import (
    aprobar_etapa,
    devolver_etapa,
)

def _es_coordinador_de_facultad(solicitud, user):
    """
    Verifica si el usuario es Coordinador Administrativo de la misma 
    facultad/dependencia que el funcionario de la solicitud.
    """
    user_func = getattr(user, "funcionario", None)
    if not user_func:
        return False
    return solicitud.funcionario.facultad_dependencia_id == user_func.facultad_dependencia_id

@method_decorator(group_required("Coordinador Administrativo"), name="dispatch")
class SolicitudesCoordListView(LoginRequiredMixin, ListView):
    """
    Lista las solicitudes de vacaciones que el Coordinador Administrativo puede ver:
    - De funcionarios que pertenecen a la misma facultad_dependencia
    - Solo aquellas que han sido aprobadas por el Jefe Inmediato (etapa JEFE aprobada)
    """
    model = SolicitudVacaciones
    template_name = "vacaciones/coord-solicitudes-list.html"
    context_object_name = "solicitudes"
    paginate_by = 20

    def get(self, request, *args, **kwargs):
        if request.htmx:
            self.object_list = self.get_queryset()
            context = self.get_context_data()
            html = render_to_string('vacaciones/partials/_tabla-coord-solicitudes.html', context, request)
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
