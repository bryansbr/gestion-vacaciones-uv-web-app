from django.urls import path, include
from .views import (
    PeriodoVacacionalListView,
    PeriodoVacacionalCreateView,
    PeriodoVacacionalUpdateView,
    PeriodoVacacionalDeleteView,
    #PeriodoVacacionalDetailView
)

app_name = "vacaciones"

urlpatterns = [
    # Rutas Web (HTML)
    path('periodos-vacacionales/', PeriodoVacacionalListView.as_view(), name="periodo_vacacional_list"),
    path('periodos-vacacionales/crear/', PeriodoVacacionalCreateView.as_view(), name="periodo_vacacional_create"),
    path('periodos-vacacionales/<int:pk>/editar/', PeriodoVacacionalUpdateView.as_view(), name="periodo_vacacional_update"),
    path('periodos-vacacionales/<int:pk>/eliminar/', PeriodoVacacionalDeleteView.as_view(), name="periodo_vacacional_delete"),
    #path('periodos-vacacionales/<int:pk>/', PeriodoVacacionalDetailView.as_view(), name="periodo_vacacional_detail"),

    # Rutas API REST
    path('api/', include('vacaciones.urls_api')),
]
