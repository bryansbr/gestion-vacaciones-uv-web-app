from datetime import date

from django import forms

from core.permissions import es_secretaria, es_jefe_inmediato
from usuarios.models import Funcionario

from .models import PeriodoVacacional, ReintegroVacaciones, SolicitudVacaciones
from .utils import get_current_date_colombia

class PeriodoVacacionalForm(forms.ModelForm):
    class Meta:
        model = PeriodoVacacional
        fields = [
            'funcionario',
            'fecha_inicio_periodo',
            'fecha_fin_periodo',
            'dias_disfrutados_periodo',
        ]
        widgets = {
            'fecha_inicio_periodo': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'fecha_fin_periodo': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'dias_disfrutados_periodo': forms.NumberInput(attrs={'class': 'form-input'}),
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data


class SolicitudVacacionesForm(forms.ModelForm):
    numero_identificacion = forms.CharField(required=False, disabled=True)
    nombre_funcionario = forms.CharField(required=False, disabled=True)
    estamento = forms.CharField(required=False, disabled=True)
    facultad_dependencia = forms.CharField(required=False, disabled=True)

    dias_derecho = forms.IntegerField(
        label='Días a los que tiene derecho',
        required=False,
        disabled=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-input bg-gray-100',
            'readonly': 'readonly'
        })
    )
    tipo_habiles = forms.BooleanField(label='Hábiles', required=False, disabled=True)
    tipo_calendario = forms.BooleanField(label='Calendario', required=False, disabled=True)

    dias_pendientes = forms.IntegerField(
        label='Días pendientes',
        required=False,
        disabled=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-input bg-gray-100',
            'readonly': 'readonly'
        })
    )
    periodos_pendientes = forms.CharField(
        required=False,
        disabled=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input bg-gray-100',
            'readonly': 'readonly'
        })
    )
    tiene_dias_pendientes = forms.BooleanField(
        label='Disfrute de días pendientes',
        required=False,
        help_text='Marque esta opción si desea solicitar vacaciones por días pendientes de reintegros aprobados'
    )

    fecha_inicio_vacaciones = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-input flatpickr-input', 'placeholder': 'Seleccionar fecha', 'autocomplete': 'off'}),
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        required=True
    )
    fecha_fin_vacaciones = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-input flatpickr-input', 'placeholder': 'Seleccionar fecha', 'autocomplete': 'off'}),
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        required=True
    )

    class Meta:
        model = SolicitudVacaciones
        fields = [
            'periodo_vacacional',
            'fecha_inicio_vacaciones',
            'fecha_fin_vacaciones',
            'fecha_pago',
            'observaciones',
            'tiene_dias_pendientes',
            'codigo_sabs',
            'fecha_solicitud'
        ]
        labels = {
            'periodo_vacacional': 'Periodo(s) vacacional(es)',
            'fecha_inicio_vacaciones': 'Fecha de inicio vacaciones',
            'fecha_fin_vacaciones': 'Fecha de fin vacaciones',
            'fecha_pago': 'Fecha de pago vacaciones',
            'codigo_sabs': 'Código SABS',
            'fecha_solicitud': 'Fecha de solicitud',
        }
        widgets = {
            'fecha_pago': forms.DateInput(attrs={
                'class': 'form-input bg-gray-100 cursor-not-allowed',
                'readonly': 'readonly',
                'disabled': 'disabled'
            }),
            'observaciones': forms.Textarea(attrs={'class': 'form-textarea'}),
            'periodo_vacacional': forms.Select(attrs={'class': 'form-select'}),
            'codigo_sabs': forms.TextInput(attrs={
                'class': 'form-input bg-gray-100 cursor-not-allowed',
                'readonly': 'readonly'
            }),
            'fecha_solicitud': forms.DateInput(attrs={
                'class': 'form-input bg-gray-100 cursor-not-allowed',
                'readonly': 'readonly'
            }),
            'numero_identificacion': forms.TextInput(attrs={
                'class': 'form-input bg-gray-100 cursor-not-allowed',
                'readonly': 'readonly',
                'disabled': 'disabled'
            }),
            'nombre_funcionario': forms.TextInput(attrs={
                'class': 'form-input bg-gray-100 cursor-not-allowed',
                'readonly': 'readonly',
                'disabled': 'disabled'
            }),
            'estamento': forms.TextInput(attrs={
                'class': 'form-input bg-gray-100 cursor-not-allowed',
                'readonly': 'readonly',
                'disabled': 'disabled'
            }),
            'facultad_dependencia': forms.TextInput(attrs={
                'class': 'form-input bg-gray-100 cursor-not-allowed',
                'readonly': 'readonly',
                'disabled': 'disabled'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        funcionario_id = kwargs.pop('funcionario_id', None)
        super().__init__(*args, **kwargs)
        
        self.user = user
        funcionario = None
        
        if self.instance and self.instance.pk:
            funcionario = self.instance.funcionario
        elif funcionario_id:
            try:
                funcionario = Funcionario.objects.get(pk=funcionario_id)
            except Funcionario.DoesNotExist:
                funcionario = None
        elif user and hasattr(user, 'funcionario'):
            funcionario = user.funcionario

        if user and es_secretaria(user) and not (self.instance and self.instance.pk) and not funcionario_id:
            secretaria_func = user.funcionario
            if secretaria_func and secretaria_func.jefe_inmediato:
                self.fields['funcionario'] = forms.ModelChoiceField(
                    queryset=Funcionario.objects.filter(jefe_inmediato=secretaria_func.jefe_inmediato),
                    widget=forms.Select(attrs={'class': 'form-select'}),
                    required=True,
                    empty_label="Seleccione un funcionario"
                )
        elif user and es_jefe_inmediato(user) and not (self.instance and self.instance.pk) and not funcionario_id:
            f = funcionario
            self.fields['funcionario'] = forms.ModelChoiceField(
                queryset=Funcionario.objects.filter(jefe_inmediato=f),
                widget=forms.Select(attrs={'class': 'form-select'}),
                required=True,
                empty_label="Seleccione un funcionario"
            )

        if funcionario:
            periodos_funcionario = PeriodoVacacional.objects.filter(funcionario=funcionario).order_by('fecha_inicio_periodo')
            self.fields['periodo_vacacional'].queryset = periodos_funcionario

            self.periodos_acumulados = None
            self.periodo_mas_antiguo = None
            self.periodo_mas_reciente = None
            self.periodo_mas_antiguo_habilitado = True
            self.periodo_mas_reciente_habilitado = True

            if periodos_funcionario.count() == 2:
                self.periodos_acumulados = list(periodos_funcionario)
                self.periodo_mas_antiguo = self.periodos_acumulados[0]
                self.periodo_mas_reciente = self.periodos_acumulados[1]
                self.periodo_mas_antiguo_habilitado = self.periodo_mas_antiguo.dias_pendientes_periodo > 0
                self.periodo_mas_reciente_habilitado = not self.periodo_mas_antiguo_habilitado

            self.initial.update({
                'numero_identificacion': funcionario.numero_identificacion,
                'nombre_funcionario': f"{funcionario.nombre} {funcionario.apellido}",
                'estamento': funcionario.estamento.nombre,
                'facultad_dependencia': funcionario.facultad_dependencia.nombre,
            })

            estamento_nombre = funcionario.estamento.nombre.lower()
            decreto = (funcionario.decreto_resolucion or '').strip()
        else:
            estamento_nombre = ''
            decreto = ''
            dias_derecho = 0

        if estamento_nombre == 'docente':
            if decreto == '1279':
                dias_derecho = 30
                self.initial['tipo_habiles'] = True
                self.initial['tipo_calendario'] = True
            elif decreto == '115':
                dias_derecho = 30
                self.initial['tipo_habiles'] = False
                self.initial['tipo_calendario'] = True
            else:
                dias_derecho = 0
                self.initial['tipo_habiles'] = False
                self.initial['tipo_calendario'] = False
        elif estamento_nombre == 'administrativo':
            dias_derecho = 15
            self.initial['tipo_habiles'] = True
            self.initial['tipo_calendario'] = False
        elif estamento_nombre == 'trabajador oficial':
            dias_derecho = 30
            self.initial['tipo_habiles'] = False
            self.initial['tipo_calendario'] = True
        else:
            dias_derecho = 0
            self.initial['tipo_habiles'] = False
            self.initial['tipo_calendario'] = False
        self.initial['dias_derecho'] = dias_derecho

        if funcionario:
            dias_pendientes = 0
            if hasattr(funcionario, 'periodos_vacacionales'):
                dias_pendientes = sum(p.dias_pendientes_periodo for p in funcionario.periodos_vacacionales.all())
            self.initial['dias_pendientes'] = dias_pendientes

            hoy = get_current_date_colombia()

            if estamento_nombre == 'docente':
                # Docentes: pago mensual el día 30
                if hoy.day <= 10:
                    if hoy.month == 12:
                        fecha_pago = date(hoy.year, 12, 30)
                    else:
                        fecha_pago = date(hoy.year, hoy.month, 30)
                else:
                    if hoy.month == 12:
                        fecha_pago = date(hoy.year + 1, 1, 30)
                    else:
                        fecha_pago = date(hoy.year, hoy.month + 1, 30)
            else:
                # Administrativos y trabajadores oficiales: pago quincenal (15 y 30)
                if hoy.day <= 3:
                    fecha_pago = date(hoy.year, hoy.month, 15)
                elif hoy.day <= 18:
                    fecha_pago = date(hoy.year, hoy.month, 30)
                else:
                    if hoy.month == 12:
                        fecha_pago = date(hoy.year + 1, 1, 15)
                    else:
                        fecha_pago = date(hoy.year, hoy.month + 1, 15)

            self.initial['fecha_pago'] = fecha_pago

            periodos_pendientes_count = PeriodoVacacional.objects.filter(
                funcionario=funcionario,
                dias_pendientes_periodo__gt=0
            ).count()

            self.initial['periodos_pendientes'] = periodos_pendientes_count

        if self.instance and self.instance.pk:
            if self.instance.fecha_inicio_vacaciones:
                self.fields['fecha_inicio_vacaciones'].initial = self.instance.fecha_inicio_vacaciones.strftime('%d/%m/%Y')
            if self.instance.fecha_fin_vacaciones:
                self.fields['fecha_fin_vacaciones'].initial = self.instance.fecha_fin_vacaciones.strftime('%d/%m/%Y')

    def clean_tiene_dias_pendientes(self):
        """
        Limpia y establece el valor de tiene_dias_pendientes basado en la lógica de negocio.
        Si no se proporciona en el POST, se establece basado en la existencia de reintegros pendientes.
        """
        tiene_dias_pendientes = self.cleaned_data.get('tiene_dias_pendientes', False)
        
        if 'tiene_dias_pendientes' not in self.data:
            funcionario = None
            if hasattr(self, 'cleaned_data') and 'funcionario' in self.cleaned_data:
                funcionario = self.cleaned_data['funcionario']
            elif 'instance' in self.__dict__ and self.instance and self.instance.funcionario:
                funcionario = self.instance.funcionario
            elif 'user' in self.__dict__ and hasattr(self.__dict__['user'], 'funcionario'):
                funcionario = self.__dict__['user'].funcionario
            
            if funcionario:
                reintegros_pendientes = ReintegroVacaciones.objects.filter(
                    funcionario=funcionario,
                    estado_solicitud='aprobado',
                    dias_pendientes__gt=0
                )
                tiene_dias_pendientes = reintegros_pendientes.exists()
        
        return tiene_dias_pendientes

    def clean(self):
        cleaned_data = super().clean()
        
        if 'funcionario' in self.fields and 'funcionario' in cleaned_data:
            funcionario_seleccionado = cleaned_data.get('funcionario')
            if funcionario_seleccionado and hasattr(funcionario_seleccionado, 'pk'):
                periodos_funcionario = PeriodoVacacional.objects.filter(funcionario=funcionario_seleccionado).order_by('fecha_inicio_periodo')
                self.fields['periodo_vacacional'].queryset = periodos_funcionario
                periodo_seleccionado = cleaned_data.get('periodo_vacacional')
                
                if periodo_seleccionado and periodo_seleccionado not in periodos_funcionario:
                    raise forms.ValidationError({'periodo_vacacional': 'El periodo vacacional seleccionado no pertenece al funcionario seleccionado.'})
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        user = getattr(self, 'user', None)
        if user and not instance.creada_por_id:
            instance.creada_por = user
        if commit:
            instance.save()
            self.save_m2m()
        return instance
