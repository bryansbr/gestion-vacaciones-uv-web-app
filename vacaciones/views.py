from django.views.generic import (
    ListView, 
    CreateView, 
    UpdateView, 
    DeleteView, 
    DetailView
)
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
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

# Actualizar periodos vacacionales
class PeriodoVacacionalUpdateView(LoginRequiredMixin, UpdateView):
    model = PeriodoVacacional
    form_class = PeriodoVacacionalForm
    template_name = "vacaciones/periodo_vacacional_form.html"
    success_url = reverse_lazy("vacaciones:periodo_vacacional_list")

# Eliminar periodos vacacionales
class PeriodoVacacionalDeleteView(LoginRequiredMixin, DeleteView):
    model = PeriodoVacacional
    template_name = "vacaciones/periodo_vacacional_confirm_delete.html"
    success_url = reverse_lazy("vacaciones:periodo_vacacional_list")

# Ver detalle del periodo vacacional (revisar si es necesario)
# class PeriodoVacacionalDetailView(LoginRequiredMixin, DetailView):
#    model = PeriodoVacacional
#    template_name = "vacaciones/periodo_vacacional_detail.html"
#    context_object_name = "periodo"
