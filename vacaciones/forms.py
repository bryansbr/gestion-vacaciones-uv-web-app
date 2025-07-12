from django import forms
from .models import PeriodoVacacional, SolicitudVacaciones
from django.contrib.auth import get_user_model
from datetime import date

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
        fecha_inicio = cleaned_data.get('fecha_inicio_periodo')
        fecha_fin = cleaned_data.get('fecha_fin_periodo')
        dias_disfrutados = cleaned_data.get('dias_disfrutados_periodo')
        funcionario = cleaned_data.get('funcionario')

        periodo = PeriodoVacacional(
            fecha_inicio_periodo=fecha_inicio,
            fecha_fin_periodo=fecha_fin,
            dias_disfrutados_periodo=dias_disfrutados,
            funcionario=funcionario
        )

        try:
            periodo.clean()
        except forms.ValidationError as e:
            for error in e.error_list:
                self.add_error(None, error.message)

        return cleaned_data

class SolicitudVacacionesForm(forms.ModelForm):
    numero_identificacion = forms.CharField(required=False, disabled=True)
    nombre_funcionario = forms.CharField(required=False, disabled=True)
    estamento = forms.CharField(required=False, disabled=True)
    facultad_dependencia = forms.CharField(required=False, disabled=True)
    dias_derecho = forms.IntegerField(label='Días a los que tiene derecho', required=False, disabled=True, widget=forms.NumberInput(attrs={
        'class': 'form-input bg-gray-100',
        'readonly': 'readonly'
    }))
    tipo_habiles = forms.BooleanField(label='Hábiles', required=False, disabled=True)
    tipo_calendario = forms.BooleanField(label='Calendario', required=False, disabled=True)
    dias_pendientes = forms.IntegerField(label='Días pendientes', required=False, disabled=True, widget=forms.NumberInput(attrs={
        'class': 'form-input bg-gray-100',
        'readonly': 'readonly'
    }))
    fecha_solicitud = forms.DateField(
        required=False,
        disabled=True,
        widget=forms.DateInput(attrs={
            'class': 'form-input bg-gray-100 cursor-not-allowed',
            'readonly': 'readonly',
            'disabled': 'disabled'
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

    class Meta:
        model = SolicitudVacaciones
        exclude = ['estado_solicitud', 'fecha_elaboracion', 'funcionario', 'total_dias_solicitados']
        widgets = {
            'fecha_inicio_vacaciones': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'fecha_fin_vacaciones': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'fecha_pago': forms.DateInput(attrs={
                'class': 'form-input bg-gray-100 cursor-not-allowed',
                'readonly': 'readonly',
                'disabled': 'disabled'
            }),
            'observaciones': forms.Textarea(attrs={'class': 'form-textarea'}),
            'periodo_vacacional': forms.Select(attrs={'class': 'form-select'}),
            'disfrute_dias_pendientes': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'codigo_sabs': forms.TextInput(attrs={'class': 'form-input', 'readonly': 'readonly'}),
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
        super().__init__(*args, **kwargs)

        if 'instance' in kwargs and kwargs['instance']:
            funcionario = kwargs['instance'].funcionario
        else:
            # Obtener el funcionario del usuario actual
            User = get_user_model()
            user = User.objects.get(id=kwargs.get('initial', {}).get('user_id'))
            funcionario = user.funcionario

        # Filtrar periodos vacacionales solo del funcionario logueado
        periodos_funcionario = PeriodoVacacional.objects.filter(funcionario=funcionario).order_by('-fecha_inicio_periodo')
        self.fields['periodo_vacacional'].queryset = periodos_funcionario

        # Establecer los valores iniciales para los campos del funcionario
        self.initial.update({
            'numero_identificacion': funcionario.numero_identificacion,
            'nombre_funcionario': f"{funcionario.nombre} {funcionario.apellido}",
            'estamento': funcionario.estamento.nombre,
            'facultad_dependencia': funcionario.facultad_dependencia.nombre,
        })
        # Calcular días a los que tiene derecho según estamento y decreto/resolución
        estamento_nombre = funcionario.estamento.nombre.lower()
        decreto = (funcionario.decreto_resolucion or '').strip()

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
        
        # Calcular días pendientes de periodos anteriores
        dias_pendientes = 0
        if hasattr(funcionario, 'periodos_vacacionales'):
            dias_pendientes = sum(p.dias_pendientes_periodo for p in funcionario.periodos_vacacionales.all())
        self.initial['dias_pendientes'] = dias_pendientes

        # Calcular automáticamente la fecha de pago
        hoy = date.today()
        
        if estamento_nombre == 'docente':
            # Docentes: pago mensual el día 30
            # Si la solicitud se hace antes del día 10, el pago es el 30 del mes actual
            # Si se hace después del día 10, el pago es el 30 del mes siguiente
            if hoy.day <= 10:
                # Pago el 30 del mes actual
                if hoy.month == 12:
                    # Diciembre: pago el 30 de diciembre
                    fecha_pago = date(hoy.year, 12, 30)
                else:
                    fecha_pago = date(hoy.year, hoy.month, 30)
            else:
                # Pago el 30 del mes siguiente
                if hoy.month == 12:
                    # Diciembre: pago el 30 de enero del año siguiente
                    fecha_pago = date(hoy.year + 1, 1, 30)
                else:
                    fecha_pago = date(hoy.year, hoy.month + 1, 30)
        else:
            # Administrativos y trabajadores oficiales: pago quincenal (15 y 30)
            if hoy.day <= 3:
                # Pago el 15 del mes actual
                fecha_pago = date(hoy.year, hoy.month, 15)
            elif hoy.day <= 18:
                # Pago el 30 del mes actual
                fecha_pago = date(hoy.year, hoy.month, 30)
            else:
                # Pago el 15 del mes siguiente
                if hoy.month == 12:
                    # Diciembre: pago el 15 de enero del año siguiente
                    fecha_pago = date(hoy.year + 1, 1, 15)
                else:
                    fecha_pago = date(hoy.year, hoy.month + 1, 15)
        
        self.initial['fecha_pago'] = fecha_pago

        # Calcular cantidad de periodos pendientes
        periodos_pendientes_count = PeriodoVacacional.objects.filter(
            funcionario=funcionario,
            dias_pendientes_periodo__gt=0
        ).count()
        self.initial['periodos_pendientes'] = periodos_pendientes_count
