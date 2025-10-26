from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from django_filters.rest_framework import DjangoFilterBackend

from .models import PeriodoVacacional, SolicitudVacaciones, ReintegroVacaciones
from .serializers import (
    PeriodoVacacionalSerializer,
    SolicitudVacacionesSerializer,
    ReintegroVacacionesSerializer,
)

class IsAdminOrReadOnly(IsAuthenticated):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)

class PeriodoVacacionalViewSet(viewsets.ModelViewSet):
    """
    API REST para gestión de Periodos Vacacionales.
    Soporta paginación, búsqueda, filtrado y ordenamiento.
    """
    queryset = PeriodoVacacional.objects.all()
    serializer_class = PeriodoVacacionalSerializer
    permission_classes = [IsAdminOrReadOnly]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['fecha_inicio_periodo', 'fecha_fin_periodo', 'funcionario']
    search_fields = [
        'funcionario__nombre',
        'funcionario__apellido',
        'funcionario__numero_identificacion',
    ]
    ordering_fields = ['fecha_inicio_periodo', 'fecha_fin_periodo', 'dias_totales_periodo']
    ordering = ['-fecha_inicio_periodo']

    def get_queryset(self):
        qs = super().get_queryset()
        u = self.request.user

        if not (u.is_staff or u.is_superuser):
            if hasattr(u, 'funcionario') and u.funcionario_id:
                return qs.filter(funcionario=u.funcionario)
            return qs.none()
        return qs


class SolicitudVacacionesViewSet(viewsets.ModelViewSet):
    """
    API REST para gestión de Solicitudes de Vacaciones.
    """
    queryset = SolicitudVacaciones.objects.all()
    serializer_class = SolicitudVacacionesSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'funcionario', 'periodo_vacacional']
    search_fields = [
        'codigo_sabs',
        'funcionario__nombre',
        'funcionario__apellido',
    ]
    ordering_fields = ['fecha_solicitud', 'fecha_inicio_vacaciones', 'total_dias_solicitados']
    ordering = ['-fecha_solicitud']

    def get_queryset(self):
        qs = super().get_queryset()
        u = self.request.user

        if not (u.is_staff or u.is_superuser):
            if hasattr(u, 'funcionario') and u.funcionario_id:
                return qs.filter(funcionario=u.funcionario)
            return qs.none()
        return qs

class ReintegroVacacionesViewSet(viewsets.ModelViewSet):
    """
    API REST para gestión de Reintegros de Vacaciones.
    """
    queryset = ReintegroVacaciones.objects.all()
    serializer_class = ReintegroVacacionesSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'funcionario', 'periodo_vacacional']
    search_fields = [
        'codigo_sabs',
        'funcionario__nombre',
        'funcionario__apellido',
    ]
    ordering_fields = ['fecha_solicitud', 'fecha_reintegro', 'dias_disfrutados']
    ordering = ['-fecha_solicitud']

    def get_queryset(self):
        qs = super().get_queryset()
        u = self.request.user

        if not (u.is_staff or u.is_superuser):
            if hasattr(u, 'funcionario') and u.funcionario_id:
                return qs.filter(funcionario=u.funcionario)
            return qs.none()
        return qs
