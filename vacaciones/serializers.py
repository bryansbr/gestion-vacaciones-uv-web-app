from django.forms import ValidationError
from rest_framework import serializers
from .models import PeriodoVacacional, SolicitudVacaciones, ReintegroVacaciones

class PeriodoVacacionalSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodoVacacional
        fields = [
            'id', 'fecha_inicio_periodo', 'fecha_fin_periodo',
            'dias_totales_periodo', 'dias_pendientes_periodo',
            'dias_disfrutados_periodo', 'funcionario'
        ]
        read_only_fields = ('dias_totales_periodo', 'dias_pendientes_periodo')

    def validate(self, data):
        periodo = PeriodoVacacional(**data)
        periodo.funcionario = data.get('funcionario')

        try:
            periodo.clean()
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)

        return data


class SolicitudVacacionesSerializer(serializers.ModelSerializer):
    class Meta:
        model = SolicitudVacaciones
        fields = [
            'id',
            'codigo_sabs',
            'fecha_solicitud',
            'fecha_inicio_vacaciones',
            'fecha_fin_vacaciones',
            'total_dias_solicitados',
            'fecha_pago',
            'observaciones',
            'tiene_dias_pendientes',
            'periodo_vacacional',
            'funcionario',
            'estado_solicitud',
        ]
        read_only_fields = ['fecha_solicitud', 'estado_solicitud']

    def validate(self, data):
        """
        Validación cruzada reutilizando el método .clean() del modelo
        """
        instance = SolicitudVacaciones(**data)

        if self.instance: instance.pk = self.instance.pk

        try:
            instance.clean()
        except serializers.ValidationError as e:
            raise e
        except Exception as e:
            raise serializers.ValidationError(str(e))

        return data

class ReintegroVacacionesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReintegroVacaciones
        fields = [
            'id',
            'codigo_sabs',
            'fecha_solicitud',
            'fecha_reintegro',
            'motivo_reintegro',
            'observaciones',
            'fecha_disfrute_desde',
            'fecha_disfrute_hasta',
            'dias_disfrutados',
            'tipo_dias_disfrutados',
            'dias_pendientes',
            'tipo_dias_pendientes',
            'periodo_vacacional',
            'solicitud_vacaciones',
            'funcionario',
            'estado_solicitud',
        ]
        read_only_fields = ('fecha_solicitud', 'estado_solicitud')
