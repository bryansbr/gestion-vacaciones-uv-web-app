from rest_framework import serializers
from .models import PeriodoVacacional

class PeriodoVacacionalSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodoVacacional
        fields = [
            'id',
            'fecha_inicio_periodo',
            'fecha_fin_periodo',
            'dias_totales_periodo',
            'dias_pendientes_periodo',
            'dias_disfrutados_periodo',
            'funcionario',
        ]
        read_only_fields = ('dias_totales_periodo', 'dias_pendientes_periodo')
