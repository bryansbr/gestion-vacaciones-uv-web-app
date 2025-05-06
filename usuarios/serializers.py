from rest_framework import serializers
from .models import Funcionario

class EstadoVacacionesSerializer(serializers.Serializer):
    antiguedad_dias = serializers.IntegerField()
    puede_solicitar = serializers.BooleanField()
    ultimo_periodo = serializers.DictField(child=serializers.IntegerField(), allow_null=True)
    