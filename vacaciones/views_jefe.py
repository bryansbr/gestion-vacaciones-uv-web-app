from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import ListView

from core.permissions import group_required
from usuarios.models import Funcionario
from vacaciones.services.flujo import (
    transicion_aprobar_por_jefe as _transicion_aprobar_por_jefe,
    transicion_devolver_por_jefe as _transicion_devolver_por_jefe,
)

from .models import HistoricoAcciones, ReintegroVacaciones, SolicitudVacaciones

def _es_jefe_de(solicitud, user):
    return getattr(solicitud.funcionario, "jefe_inmediato_id", None) == getattr(user, "id", None)

@method_decorator(group_required("Jefe Inmediato"), name="dispatch")
class SolicitudesJefeListView(LoginRequiredMixin, ListView):
    model = SolicitudVacaciones
    template_name = "vacaciones/solicitudes-jefe-list.html"
    context_object_name = "solicitudes"
    paginate_by = 20

    def get_queryset(self):
        jefe_func = getattr(self.request.user, "funcionario", None)

        if jefe_func is None:
            jefe_func = (Funcionario.objects.filter(usuario=self.request.user).first()
                         or Funcionario.objects.filter(user=self.request.user).first())
        if jefe_func is None:
            jefe_func = Funcionario.objects.filter(correo_institucional=self.request.user.email).first()

        if jefe_func is None:
            return SolicitudVacaciones.objects.none()

        qs = (SolicitudVacaciones.objects
              .select_related("funcionario", "periodo_vacacional")
              .filter(funcionario__jefe_inmediato=jefe_func)
              .order_by("-fecha_solicitud", "-id"))

        q = self.request.GET.get("q", "").strip()
        estado = self.request.GET.get("estado", "").strip()

        if q:
            qs = qs.filter(
                Q(codigo_sabs__icontains=q) |
                Q(funcionario__nombres__icontains=q) |
                Q(funcionario__apellidos__icontains=q)
            )
        if estado:
            qs = qs.filter(estado_solicitud=estado)

        return qs

def solicitud_pdf(request, pk):
    solicitud = get_object_or_404(SolicitudVacaciones, pk=pk)
    if not _es_jefe_de(solicitud, request.user) and not request.user.is_superuser:
        return HttpResponseForbidden()
    return redirect(solicitud.pdf_url)

@group_required("Jefe Inmediato")
@transaction.atomic
def aprobar_solicitud(request, pk):
    if request.method != "POST":
        return HttpResponseBadRequest("Método no permitido")
    solicitud = get_object_or_404(SolicitudVacaciones, pk=pk)
    if not _es_jefe_de(solicitud, request.user) and not request.user.is_superuser:
        return HttpResponseForbidden()

    # Reglas de transición: de "PENDIENTE_JEFE" → "PENDIENTE_COORD"
    ok, msg = _transicion_aprobar_por_jefe(solicitud, request.user, comentario=request.POST.get("comentario", ""))
    status = 200 if ok else 400
    messages.add_message(request, messages.INFO if ok else messages.ERROR, msg)

    if request.headers.get("HX-Request"):
        return render(request, "vacaciones/partials/_solicitud-row-jefe.html", {"s": solicitud})
    return redirect(reverse("vacaciones:solicitudes_jefe"))

@group_required("Jefe Inmediato")
@transaction.atomic
def devolver_solicitud(request, pk):
    if request.method != "POST":
        return HttpResponseBadRequest("Método no permitido")
    solicitud = get_object_or_404(SolicitudVacaciones, pk=pk)
    if not _es_jefe_de(solicitud, request.user) and not request.user.is_superuser:
        return HttpResponseForbidden()

    motivo = request.POST.get("comentario", "").strip()
    ok, msg = _transicion_devolver_por_jefe(solicitud, request.user, comentario=motivo)
    status = 200 if ok else 400
    messages.add_message(request, messages.INFO if ok else messages.ERROR, msg)

    if request.headers.get("HX-Request"):
        return render(request, "vacaciones/partials/solicitud-row-jefe.html", {"s": solicitud})
    return redirect(reverse("vacaciones:solicitudes_jefe"))
