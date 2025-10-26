from django.core.exceptions import ValidationError
from rest_framework import serializers

from .models import PeriodoVacacional, SolicitudVacaciones, ReintegroVacaciones

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

    def validate(self, data):
        """
        Reutiliza la validación del modelo (clean), soportando creates y updates parciales.
        """
        instance = self.instance or PeriodoVacacional()

        for k, v in data.items():
            setattr(instance, k, v)

        try:
            instance.clean()
        except ValidationError as e:
            # e.message_dict (por campo) o e.messages (lista)
            raise serializers.ValidationError(getattr(e, "message_dict", e.messages))
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
            'estado',
        ]
        read_only_fields = ['codigo_sabs', 'fecha_solicitud', 'estado']

    def validate(self, data):
        """
        Validación cruzada reutilizando el método .clean() del modelo.
        Soporta creates y updates parciales (PATCH).
        """
        instance = self.instance or SolicitudVacaciones()
        for k, v in data.items():
            setattr(instance, k, v)

        try:
            instance.clean()
        except ValidationError as e:
            raise serializers.ValidationError(getattr(e, "message_dict", e.messages))
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
            'estado',
        ]
        read_only_fields = ('codigo_sabs', 'fecha_solicitud', 'estado')

    def validate(self, data):
        """
        Si necesitas validar reglas adicionales del reintegro, reusa clean() del modelo.
        (Es opcional; incluyo el patrón por consistencia.)
        """
        instance = self.instance or ReintegroVacaciones()
        for k, v in data.items():
            setattr(instance, k, v)

        try:
            if hasattr(instance, "clean"):
                instance.clean()
        except ValidationError as e:
            raise serializers.ValidationError(getattr(e, "message_dict", e.messages))
        return data
