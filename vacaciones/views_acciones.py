from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from .models import SolicitudVacaciones, ReintegroVacaciones
from .permissions import scope_queryset_for

LISTADO_SOLICITUDES = "vacaciones:solicitud-vacaciones-list"

# ---- Solicitudes ----
@login_required
def enviar_solicitud(request, pk):
    if request.method != "POST":
        return redirect(LISTADO_SOLICITUDES)

    obj = get_object_or_404(
        scope_queryset_for(request.user, SolicitudVacaciones.objects.all()),
        pk=pk
    )
    try:
        obj.enviar(request.user)
        messages.success(request, "Solicitud enviada a Jefe Inmediato.")
    except Exception as e:
        messages.error(request, str(e))
    return redirect(LISTADO_SOLICITUDES)

@login_required
def aprobar_solicitud(request, pk):
    if request.method != "POST":
        return redirect(LISTADO_SOLICITUDES)

    obj = get_object_or_404(
        scope_queryset_for(request.user, SolicitudVacaciones.objects.all()),
        pk=pk
    )
    try:
        obj.aprobar(request.user)
        messages.success(request, "Acción realizada.")
    except Exception as e:
        messages.error(request, str(e))
    return redirect(LISTADO_SOLICITUDES)

@login_required
def devolver_solicitud(request, pk):
    if request.method != "POST":
        return redirect(LISTADO_SOLICITUDES)

    obj = get_object_or_404(
        scope_queryset_for(request.user, SolicitudVacaciones.objects.all()),
        pk=pk
    )
    try:
        obj.devolver(request.user, comentario=request.POST.get("comentario", ""))
        messages.info(request, "Solicitud devuelta al funcionario.")
    except Exception as e:
        messages.error(request, str(e))
    return redirect(LISTADO_SOLICITUDES)

@login_required
def rechazar_solicitud(request, pk):
    if request.method != "POST":
        return redirect(LISTADO_SOLICITUDES)

    obj = get_object_or_404(
        scope_queryset_for(request.user, SolicitudVacaciones.objects.all()),
        pk=pk
    )
    try:
        obj.rechazar(request.user, comentario=request.POST.get("comentario", ""))
        messages.warning(request, "Solicitud rechazada.")
    except Exception as e:
        messages.error(request, str(e))
    return redirect(LISTADO_SOLICITUDES)

# ---- Reintegros ----
@login_required
def enviar_reintegro(request, pk):
    if request.method != "POST":
        return redirect(LISTADO_SOLICITUDES)

    obj = get_object_or_404(
        scope_queryset_for(request.user, ReintegroVacaciones.objects.all()),
        pk=pk
    )
    try:
        obj.enviar(request.user)
        messages.success(request, "Reintegro enviado a Jefe Inmediato.")
    except Exception as e:
        messages.error(request, str(e))
    return redirect(LISTADO_SOLICITUDES)

@login_required
def aprobar_reintegro(request, pk):
    if request.method != "POST":
        return redirect(LISTADO_SOLICITUDES)

    obj = get_object_or_404(
        scope_queryset_for(request.user, ReintegroVacaciones.objects.all()),
        pk=pk
    )
    try:
        obj.aprobar(request.user)
        messages.success(request, "Acción realizada.")
    except Exception as e:
        messages.error(request, str(e))
    return redirect(LISTADO_SOLICITUDES)

@login_required
def devolver_reintegro(request, pk):
    if request.method != "POST":
        return redirect(LISTADO_SOLICITUDES)

    obj = get_object_or_404(
        scope_queryset_for(request.user, ReintegroVacaciones.objects.all()),
        pk=pk
    )
    try:
        obj.devolver(request.user, comentario=request.POST.get("comentario", ""))
        messages.info(request, "Reintegro devuelto al funcionario.")
    except Exception as e:
        messages.error(request, str(e))
    return redirect(LISTADO_SOLICITUDES)

@login_required
def rechazar_reintegro(request, pk):
    if request.method != "POST":
        return redirect(LISTADO_SOLICITUDES)

    obj = get_object_or_404(
        scope_queryset_for(request.user, ReintegroVacaciones.objects.all()),
        pk=pk
    )
    try:
        obj.rechazar(request.user, comentario=request.POST.get("comentario", ""))
        messages.warning(request, "Reintegro rechazado.")
    except Exception as e:
        messages.error(request, str(e))
    return redirect(LISTADO_SOLICITUDES)
