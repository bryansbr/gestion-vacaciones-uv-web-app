from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.timezone import now
from datetime import date, datetime
from .models import PeriodoVacacional, SolicitudVacaciones, generar_codigo_sabs, ReintegroVacaciones
from .forms import PeriodoVacacionalForm, SolicitudVacacionesForm
import holidays
import json
import pytz

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
        colombia_tz = pytz.timezone('America/Bogota')
        hoy_colombia = datetime.now(colombia_tz).date()
        initial['fecha_solicitud'] = hoy_colombia
        initial['codigo_sabs'] = generar_codigo_sabs('VAC', hoy_colombia.year)
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

        # Verificar si el funcionario tiene periodos vacacionales
        periodos_vacacionales = PeriodoVacacional.objects.filter(funcionario=funcionario)
        context['tiene_periodos_vacacionales'] = periodos_vacacionales.exists()
        
        # Si no tiene periodos, no mostrar reintegros ni otros datos
        if not context['tiene_periodos_vacacionales']:
            context['reintegros_pendientes'] = json.dumps([])
            context['tiene_reintegros_pendientes'] = False
            context['periodos_acumulados'] = None
            context['plazo_solicitud'] = None
            context['mostrar_alerta_periodos_acumulados'] = False
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
        )
        
        # Una solicitud se considera "culminada" si tiene un reintegro asociado
        solicitudes_sin_reintegro = []
        for solicitud in solicitudes_activas:
            # Verificar si existe un reintegro asociado a esta solicitud
            tiene_reintegro = ReintegroVacaciones.objects.filter(
                solicitud_vacaciones=solicitud,
                estado_solicitud='aprobado'
            ).exists()
            
            if not tiene_reintegro:
                solicitudes_sin_reintegro.append(solicitud)
        
        context['puede_crear_solicitud'] = len(solicitudes_sin_reintegro) == 0
        context['solicitud_activa'] = solicitudes_sin_reintegro[0] if solicitudes_sin_reintegro else None

        form = context.get('form')

        # Lógica para determinar si mostrar alerta de periodos acumulados
        context['mostrar_alerta_periodos_acumulados'] = False
        
        if hasattr(form, 'periodos_acumulados') and form.periodos_acumulados:
            context['periodos_acumulados'] = form.periodos_acumulados
            context['periodo_mas_antiguo'] = form.periodo_mas_antiguo
            context['periodo_mas_reciente'] = form.periodo_mas_reciente
            context['periodo_mas_antiguo_habilitado'] = form.periodo_mas_antiguo_habilitado
            context['periodo_mas_reciente_habilitado'] = form.periodo_mas_reciente_habilitado
            
            # Solo mostrar alerta de periodos acumulados si:
            # 1. No hay solicitud activa pendiente
            # 2. No se ha hecho ninguna solicitud sobre los periodos acumulados
            if context['puede_crear_solicitud']:
                # Verificar si ya se ha hecho alguna solicitud sobre los periodos acumulados
                solicitudes_periodos_acumulados = SolicitudVacaciones.objects.filter(
                    funcionario=funcionario,
                    periodo_vacacional__in=[form.periodo_mas_antiguo, form.periodo_mas_reciente]
                ).exists()
                
                # Solo mostrar la alerta si no se ha hecho ninguna solicitud sobre los periodos acumulados
                context['mostrar_alerta_periodos_acumulados'] = not solicitudes_periodos_acumulados

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

        # Verificar si el funcionario tiene periodos vacacionales antes de procesar el formulario
        funcionario = self.request.user.funcionario
        periodos_vacacionales = PeriodoVacacional.objects.filter(funcionario=funcionario)
        
        if not periodos_vacacionales.exists():
            messages.error(request, "No puede crear una solicitud de vacaciones sin tener periodos vacacionales registrados.")
            return self.form_invalid(form)

        # Verificar si ya tiene una solicitud activa sin reintegro asociado
        solicitudes_activas = SolicitudVacaciones.objects.filter(
            funcionario=funcionario,
            estado_solicitud__in=['pendiente', 'en_revision', 'aprobado']
        )
        
        solicitudes_sin_reintegro = []
        for solicitud in solicitudes_activas:
            tiene_reintegro = ReintegroVacaciones.objects.filter(
                solicitud_vacaciones=solicitud,
                estado_solicitud='aprobado'
            ).exists()
            
            if not tiene_reintegro:
                solicitudes_sin_reintegro.append(solicitud)
        
        if solicitudes_sin_reintegro:
            messages.error(request, "Ya tiene una solicitud de vacaciones activa. Debe culminar el disfrute del periodo actual antes de crear una nueva solicitud.")
            return self.form_invalid(form)

        form.instance.funcionario = funcionario
        
        # Asignar la fecha de solicitud (hoy en Colombia UTC-5)
        colombia_tz = pytz.timezone('America/Bogota')
        hoy_colombia = datetime.now(colombia_tz).date()
        form.instance.fecha_solicitud = hoy_colombia
        
        # Determinar si tiene días pendientes basado en reintegros aprobados
        reintegros_pendientes = ReintegroVacaciones.objects.filter(
            funcionario=funcionario,
            estado_solicitud='aprobado',
            dias_pendientes__gt=0
        )
        
        # Usar el valor del formulario si está presente, sino calcular automáticamente
        if 'tiene_dias_pendientes' in request.POST:
            form.instance.tiene_dias_pendientes = request.POST.get('tiene_dias_pendientes') == 'on'
        else:
            form.instance.tiene_dias_pendientes = reintegros_pendientes.exists()
        
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form):
        try:
            # Guardar la instancia
            self.object = form.save()
            messages.success(self.request, "Solicitud registrada correctamente.")
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f"Error al guardar la solicitud: {e}")
            return self.form_invalid(form)
    
class SolicitudVacacionesListView(LoginRequiredMixin, ListView):
    model = SolicitudVacaciones
    template_name = "vacaciones/solicitud-vacaciones-list.html"
    context_object_name = "solicitudes"

    def get_queryset(self):
        return SolicitudVacaciones.objects.filter(funcionario=self.request.user.funcionario).order_by('-fecha_solicitud')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        funcionario = self.request.user.funcionario
        
        # Verificar si el funcionario tiene una solicitud activa (sin reintegro asociado)
        solicitudes_activas = SolicitudVacaciones.objects.filter(
            funcionario=funcionario,
            estado_solicitud__in=['pendiente', 'en_revision', 'aprobado']
        )
        
        # Una solicitud se considera "culminada" si tiene un reintegro asociado
        solicitudes_sin_reintegro = []
        for solicitud in solicitudes_activas:
            # Verificar si existe un reintegro asociado a esta solicitud
            tiene_reintegro = ReintegroVacaciones.objects.filter(
                solicitud_vacaciones=solicitud,
                estado_solicitud='aprobado'
            ).exists()
            
            if not tiene_reintegro:
                solicitudes_sin_reintegro.append(solicitud)
        
        context['puede_crear_solicitud'] = len(solicitudes_sin_reintegro) == 0
        context['solicitud_activa'] = solicitudes_sin_reintegro[0] if solicitudes_sin_reintegro else None
        
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
        years = [date.today().year, date.today().year + 1]
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
        
        # Si no tiene periodos, no mostrar reintegros ni otros datos
        if not context['tiene_periodos_vacacionales']:
            context['reintegros_pendientes'] = json.dumps([])
            context['tiene_reintegros_pendientes'] = False
            context['periodos_acumulados'] = None
            context['plazo_solicitud'] = None
            context['mostrar_alerta_periodos_acumulados'] = False
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

        # EN MODO EDICIÓN: No se ejecutan validaciones de solicitud activa
        # Estas validaciones solo aplican para creación de nuevas solicitudes
        context['puede_crear_solicitud'] = True  # Siempre True en edición
        context['solicitud_activa'] = None  # No hay solicitud activa en edición

        form = context.get('form')

        # Lógica para determinar si mostrar alerta de periodos acumulados
        context['mostrar_alerta_periodos_acumulados'] = False
        
        if hasattr(form, 'periodos_acumulados') and form.periodos_acumulados:
            context['periodos_acumulados'] = form.periodos_acumulados
            context['periodo_mas_antiguo'] = form.periodo_mas_antiguo
            context['periodo_mas_reciente'] = form.periodo_mas_reciente
            context['periodo_mas_antiguo_habilitado'] = form.periodo_mas_antiguo_habilitado
            context['periodo_mas_reciente_habilitado'] = form.periodo_mas_reciente_habilitado

        # EN MODO EDICIÓN: No se muestran alertas de plazo de solicitud
        # Estas alertas solo aplican para creación de nuevas solicitudes
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
    years = [date.today().year, date.today().year + 1]
    festivos = []

    for y in years:
        festivos += [d.strftime('%d/%m/%Y') for d in holidays.Colombia(years=[y]).keys()]
        
    festivos_json = json.dumps(festivos)

    return render(request, 'vacaciones/solicitud-vacaciones-form.html', {'festivos_colombia': festivos_json})
