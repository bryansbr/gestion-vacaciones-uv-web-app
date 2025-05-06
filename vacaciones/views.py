from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .models import PeriodoVacacional
from .forms import PeriodoVacacionalForm

# Listar periodos vacacionales
class PeriodoVacacionalListView(LoginRequiredMixin, ListView):
    model = PeriodoVacacional
    template_name = "vacaciones/periodo_vacacional_list.html"
    context_object_name = "periodos"

# Crear periodos vacacionales
class PeriodoVacacionalCreateView(LoginRequiredMixin, CreateView):
    model = PeriodoVacacional
    form_class = PeriodoVacacionalForm
    template_name = "vacaciones/periodo_vacacional_form.html"
    success_url = reverse_lazy("vacaciones:periodo_vacacional_list")

    def form_valid(self, form):
        messages.success(self.request, "Periodo vacacional creado correctamente.")
        return super().form_valid(form)

# Actualizar periodos vacacionales
class PeriodoVacacionalUpdateView(LoginRequiredMixin, UpdateView):
    model = PeriodoVacacional
    form_class = PeriodoVacacionalForm
    template_name = "vacaciones/periodo_vacacional_form.html"
    success_url = reverse_lazy("vacaciones:periodo_vacacional_list")

    def form_valid(self, form):
        messages.success(self.request, "Periodo vacacional actualizado correctamente.")
        return super().form_valid(form)

# Eliminar periodos vacacionales
class PeriodoVacacionalDeleteView(LoginRequiredMixin, DeleteView):
    model = PeriodoVacacional
    template_name = "vacaciones/periodo_vacacional_confirm_delete.html"
    success_url = reverse_lazy("vacaciones:periodo_vacacional_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Periodo vacacional eliminado correctamente.")
        return super().delete(request, *args, **kwargs)
