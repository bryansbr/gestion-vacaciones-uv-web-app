from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .models import PeriodoVacacional, SolicitudVacaciones, generar_codigo_sabs
from .forms import PeriodoVacacionalForm, SolicitudVacacionesForm
from django.utils.timezone import now

# -----------------------------------------
# MODELO: PeriodoVacacional
# -----------------------------------------
class PeriodoVacacionalListView(LoginRequiredMixin, ListView):
    model = PeriodoVacacional
    template_name = "vacaciones/periodo_vacacional_list.html"
    context_object_name = "periodos"

class PeriodoVacacionalCreateView(LoginRequiredMixin, CreateView):
    model = PeriodoVacacional
    form_class = PeriodoVacacionalForm
    template_name = "vacaciones/periodo_vacacional_form.html"
    success_url = reverse_lazy("vacaciones:periodo_vacacional_list")

    def form_valid(self, form):
        messages.success(self.request, "Periodo vacacional creado correctamente.")
        return super().form_valid(form)

class PeriodoVacacionalUpdateView(LoginRequiredMixin, UpdateView):
    model = PeriodoVacacional
    form_class = PeriodoVacacionalForm
    template_name = "vacaciones/periodo_vacacional_form.html"
    success_url = reverse_lazy("vacaciones:periodo_vacacional_list")

    def form_valid(self, form):
        messages.success(self.request, "Periodo vacacional actualizado correctamente.")
        return super().form_valid(form)

class PeriodoVacacionalDeleteView(LoginRequiredMixin, DeleteView):
    model = PeriodoVacacional
    template_name = "vacaciones/periodo_vacacional_confirm_delete.html"
    success_url = reverse_lazy("vacaciones:periodo_vacacional_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Periodo vacacional eliminado correctamente.")
        return super().delete(request, *args, **kwargs)

# -----------------------------------------
# MODELO: SolicitudVacaciones
# -----------------------------------------
class SolicitudVacacionesCreateView(LoginRequiredMixin, CreateView):
    model = SolicitudVacaciones
    form_class = SolicitudVacacionesForm
    template_name = "vacaciones/solicitud_vacaciones_form.html"
    success_url = reverse_lazy("vacaciones:solicitud_vacaciones_list")

    def get_initial(self):
        initial = super().get_initial()
        initial['codigo_sabs'] = generar_codigo_sabs('VAC', now().year)
        return initial

    def form_valid(self, form):
        form.instance.funcionario = self.request.user.funcionario
        messages.success(self.request, "Solicitud registrada correctamente.")
        return super().form_valid(form)
    
class SolicitudVacacionesListView(LoginRequiredMixin, ListView):
    model = SolicitudVacaciones
    template_name = "vacaciones/solicitud_vacaciones_list.html"
    context_object_name = "solicitudes"

    def get_queryset(self):
        return SolicitudVacaciones.objects.filter(funcionario=self.request.user.funcionario).order_by('-fecha_elaboracion')

class SolicitudVacacionesUpdateView(LoginRequiredMixin, UpdateView):
    model = SolicitudVacaciones
    form_class = SolicitudVacacionesForm
    template_name = "vacaciones/solicitud_vacaciones_form.html"
    success_url = reverse_lazy("vacaciones:solicitud_vacaciones_list")

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
    template_name = "vacaciones/solicitud_vacaciones_confirm_delete.html"
    success_url = reverse_lazy("vacaciones:solicitud_vacaciones_list")

    def get_queryset(self):
        return SolicitudVacaciones.objects.filter(
            funcionario=self.request.user.funcionario,
            estado_solicitud='pendiente'
        )

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Solicitud eliminada correctamente.")
        return super().delete(request, *args, **kwargs)
