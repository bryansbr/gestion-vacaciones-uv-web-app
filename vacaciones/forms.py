from django import forms
from .models import PeriodoVacacional

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
