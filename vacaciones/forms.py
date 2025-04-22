from django import forms
from .models import PeriodoVacacional

class PeriodoVacacionalForm(forms.ModelForm):
    class Meta:
        model = PeriodoVacacional
        fields = [
            'funcionario',
            'fecha_inicio_periodo',
            'fecha_fin_periodo',
            'dias_totales_periodo',
            'dias_pendientes_periodo',
            'dias_disfrutados_periodo',
        ]
        widgets = {
            'fecha_inicio_periodo': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'fecha_fin_periodo': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'dias_totales_periodo': forms.NumberInput(attrs={'class': 'form-input'}),
            'dias_pendientes_periodo': forms.NumberInput(attrs={'class': 'form-input'}),
            'dias_disfrutados_periodo': forms.NumberInput(attrs={'class': 'form-input'}),
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()

        fecha_inicio = cleaned_data.get('fecha_inicio_periodo')
        fecha_fin = cleaned_data.get('fecha_fin_periodo')
        dias_totales = cleaned_data.get('dias_totales_periodo')
        dias_pendientes = cleaned_data.get('dias_pendientes_periodo')
        dias_disfrutados = cleaned_data.get('dias_disfrutados_periodo')

        # Validación de fechas
        if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
            self.add_error('fecha_inicio_periodo', "La fecha de inicio no puede ser posterior a la fecha de fin.")

        # Validación de días
        if dias_totales is not None and dias_pendientes is not None and dias_disfrutados is not None:
            if dias_pendientes + dias_disfrutados > dias_totales:
                self.add_error('dias_totales_periodo', "La suma de días pendientes y disfrutados no puede ser mayor que los días totales.")

        return cleaned_data
