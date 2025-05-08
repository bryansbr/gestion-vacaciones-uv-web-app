from rest_framework import serializers

class UltimoPeriodoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    fecha_inicio = serializers.DateField()
    fecha_fin = serializers.DateField()
    dias_totales = serializers.IntegerField()
    dias_pendientes = serializers.IntegerField()
    dias_disfrutados = serializers.IntegerField()

class EstadoVacacionesSerializer(serializers.Serializer):
    antiguedad_dias = serializers.IntegerField()
    puede_solicitar = serializers.BooleanField()
    dias_pendientes_totales = serializers.IntegerField()
    ultimo_periodo = UltimoPeriodoSerializer(allow_null=True)
