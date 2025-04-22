from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from .models import PeriodoVacacional
from .serializers import PeriodoVacacionalSerializer

class PeriodoVacacionalViewSet(viewsets.ModelViewSet):
    queryset = PeriodoVacacional.objects.all()
    serializer_class = PeriodoVacacionalSerializer
    permission_classes = [IsAuthenticated]

    # Filtros exactos
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['funcionario', 'fecha_inicio_periodo', 'fecha_fin_periodo']

    # Campos para búsqueda
    search_fields = ['funcionario__nombre', 'funcionario__apellido']

    # Campos de ordenamiento
    ordering_fields = ['fecha_inicio_periodo', 'fecha_fin_periodo', 'dias_totales_periodo']
    ordering = ['fecha_inicio_periodo']
