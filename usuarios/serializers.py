from rest_framework import serializers

class EstadoVacacionesSerializer(serializers.Serializer):
    antiguedad_dias = serializers.IntegerField()
    puede_solicitar = serializers.BooleanField()
    dias_pendientes_totales = serializers.IntegerField()

    ultimo_periodo = serializers.DictField(
        child=serializers.CharField(allow_null=True),
        allow_null=True
    )
