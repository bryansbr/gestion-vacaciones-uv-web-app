from rest_framework import serializers
from .models import PeriodoVacacional

class PeriodoVacacionalSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodoVacacional
        fields = '__all__'
