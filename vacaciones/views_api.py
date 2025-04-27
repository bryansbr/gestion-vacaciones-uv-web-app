from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import PeriodoVacacional
from .serializers import PeriodoVacacionalSerializer

class PeriodoVacacionalViewSet(viewsets.ModelViewSet):
    """
    API REST para gestión de Periodos Vacacionales.
    Soporta paginación, búsqueda, filtrado y ordenamiento.
    """
    queryset = PeriodoVacacional.objects.all()
    serializer_class = PeriodoVacacionalSerializer
    permission_classes = [IsAuthenticated]

    # Filtros
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    filterset_fields = ['fecha_inicio_periodo', 'fecha_fin_periodo', 'funcionario']

    # Búsqueda
    search_fields = [
        'funcionario__nombre',
        'funcionario__apellido',
        'funcionario__numero_identificacion'
    ]

    # Ordenamiento
    ordering_fields = ['fecha_inicio_periodo', 'fecha_fin_periodo', 'dias_totales_periodo']
    ordering = ['fecha_inicio_periodo']
