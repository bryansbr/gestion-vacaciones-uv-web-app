from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.timezone import now
from datetime import date
from .models import PeriodoVacacional, SolicitudVacaciones, generar_codigo_sabs, ReintegroVacaciones
from .forms import PeriodoVacacionalForm, SolicitudVacacionesForm
import holidays
import json

# -----------------------------------------
# VISTA: PeriodoVacacional
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
# VISTA: Crear SolicitudVacaciones
# -----------------------------------------
class SolicitudVacacionesCreateView(LoginRequiredMixin, CreateView):
    model = SolicitudVacaciones
    form_class = SolicitudVacacionesForm
    template_name = "vacaciones/solicitud_vacaciones_form.html"
    success_url = reverse_lazy("vacaciones:solicitud_vacaciones_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['initial'] = kwargs.get('initial', {})
        kwargs['initial']['user_id'] = self.request.user.id
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial['fecha_solicitud'] = now().date()
        initial['codigo_sabs'] = generar_codigo_sabs('VAC', now().year)
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        years = [date.today().year, date.today().year + 1]
        festivos = []

        for y in years:
            festivos += [d.strftime('%d/%m/%Y') for d in holidays.Colombia(years=[y]).keys()]
        
        context['festivos_colombia'] = json.dumps(festivos)

        funcionario = self.request.user.funcionario
        context['funcionario_estamento'] = funcionario.estamento.nombre.lower()
        context['funcionario_decreto'] = (funcionario.decreto_resolucion or '').strip()

        # Reintegros aprobados con días pendientes
        reintegros_pendientes = ReintegroVacaciones.objects.filter(
            funcionario=funcionario,
            estado_solicitud='aprobado',
            dias_pendientes__gt=0
        ).order_by('-fecha_solicitud')

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

        if hasattr(form, 'periodos_acumulados') and form.periodos_acumulados:
            context['periodos_acumulados'] = form.periodos_acumulados
            context['periodo_mas_antiguo'] = form.periodo_mas_antiguo
            context['periodo_mas_reciente'] = form.periodo_mas_reciente
            context['periodo_mas_antiguo_habilitado'] = form.periodo_mas_antiguo_habilitado
            context['periodo_mas_reciente_habilitado'] = form.periodo_mas_reciente_habilitado

        hoy = date.today()
        estamento = funcionario.estamento.nombre.lower()

        if estamento == 'docente':
            if hoy.day <= 10:
                context['plazo_solicitud'] = (
                    "Recuerde. Por reglamentación, si realiza la solicitud hoy deberá esperar "
                    "hasta el día 1º del mes siguiente para disfrutar sus vacaciones."
                )
            else:
                context['plazo_solicitud'] = (
                    "Recuerde. Por reglamentación, si realiza la solicitud hoy deberá esperar "
                    "hasta el día 1º del mes subsiguiente para disfrutar sus vacaciones."
                )
        else:
            if hoy.day <= 3:
                context['plazo_solicitud'] = "Puede solicitar vacaciones hasta el día 3 para salir el 16 del mes actual"
            elif hoy.day <= 17:
                context['plazo_solicitud'] = "Puede solicitar vacaciones hasta el día 17 para salir el 1º del mes siguiente"
            else:
                context['plazo_solicitud'] = "Debe esperar hasta el 16 del mes siguiente para solicitar vacaciones"

        return context

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()

        form.instance.funcionario = self.request.user.funcionario

        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form):
        messages.success(self.request, "Solicitud registrada correctamente.")
        return super().form_valid(form)
    
class SolicitudVacacionesListView(LoginRequiredMixin, ListView):
    model = SolicitudVacaciones
    template_name = "vacaciones/solicitud_vacaciones_list.html"
    context_object_name = "solicitudes"

    def get_queryset(self):
        return SolicitudVacaciones.objects.filter(funcionario=self.request.user.funcionario).order_by('-fecha_solicitud')

class SolicitudVacacionesUpdateView(LoginRequiredMixin, UpdateView):
    model = SolicitudVacaciones
    form_class = SolicitudVacacionesForm
    template_name = "vacaciones/solicitud_vacaciones_form.html"
    success_url = reverse_lazy("vacaciones:solicitud_vacaciones_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['initial'] = kwargs.get('initial', {})
        kwargs['initial']['user_id'] = self.request.user.id
        return kwargs

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

def solicitud_vacaciones_create(request):
    years = [date.today().year, date.today().year + 1]
    festivos = []

    for y in years:
        festivos += [d.strftime('%d/%m/%Y') for d in holidays.Colombia(years=[y]).keys()]
        
    festivos_json = json.dumps(festivos)

    return render(request, 'vacaciones/solicitud_vacaciones_form.html', {'festivos_colombia': festivos_json})
