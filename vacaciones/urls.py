from django.urls import path, include
from .views import (
    PeriodoVacacionalListView,
    PeriodoVacacionalCreateView,
    PeriodoVacacionalUpdateView,
    PeriodoVacacionalDeleteView,
    PeriodoVacacionalDetailView,
)
from .views_api import PeriodoVacacionalViewSet
from rest_framework.routers import DefaultRouter

app_name = "vacaciones"

router = DefaultRouter()
router.register(r'periodos', PeriodoVacacionalViewSet, basename='periodos')

urlpatterns = [
    # Frontend (templates HTML)
    path('periodos/', PeriodoVacacionalListView.as_view(), name='periodo_vacacional_list'),
    path('periodos/nuevo/', PeriodoVacacionalCreateView.as_view(), name='periodo_vacacional_create'),
    path('periodos/<int:pk>/editar/', PeriodoVacacionalUpdateView.as_view(), name='periodo_vacacional_update'),
    path('periodos/<int:pk>/eliminar/', PeriodoVacacionalDeleteView.as_view(), name='periodo_vacacional_delete'),
    path('periodos/<int:pk>/', PeriodoVacacionalDetailView.as_view(), name='periodo_vacacional_detail'),

    # API REST
    path('api/', include(router.urls)),
]
