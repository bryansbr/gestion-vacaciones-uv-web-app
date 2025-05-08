from rest_framework.routers import DefaultRouter
from .views_api import (
    PeriodoVacacionalViewSet, 
    SolicitudVacacionesViewSet, 
    ReintegroVacacionesViewSet
)

router = DefaultRouter()

router.register(r'periodos-vacacionales', PeriodoVacacionalViewSet, basename='periodovacacional')
router.register(r'solicitudes-vacaciones', SolicitudVacacionesViewSet, basename='solicitudvacaciones')
router.register(r'reintegros-vacaciones', ReintegroVacacionesViewSet, basename='reintegrovacaciones')

urlpatterns = router.urls
