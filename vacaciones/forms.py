from django import forms
from .models import PeriodoVacacional, SolicitudVacaciones

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
    total_dias_solicitados = forms.IntegerField(required=True, widget=forms.NumberInput(attrs={
        'class': 'form-input bg-gray-100',
        'readonly': 'readonly'
    }))

    class Meta:
        model = SolicitudVacaciones
        exclude = ['estado_solicitud', 'fecha_elaboracion', 'funcionario']
        widgets = {
            'fecha_inicio_vacaciones': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'fecha_fin_vacaciones': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'tipo_dias_solicitados': forms.Select(attrs={'class': 'form-select'}),
            'quincena_pago': forms.Select(attrs={'class': 'form-select'}),
            'mes_pago': forms.NumberInput(attrs={'class': 'form-input'}),
            'anio_pago': forms.NumberInput(attrs={'class': 'form-input'}),
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
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=kwargs.get('initial', {}).get('user_id'))
            funcionario = user.funcionario

        # Establecer los valores iniciales para los campos del funcionario
        self.initial.update({
            'numero_identificacion': funcionario.numero_identificacion,
            'nombre_funcionario': f"{funcionario.nombre} {funcionario.apellido}",
            'estamento': funcionario.estamento.nombre,
            'facultad_dependencia': funcionario.facultad_dependencia.nombre,
        })
