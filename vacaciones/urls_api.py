from rest_framework.routers import DefaultRouter
from .views_api import PeriodoVacacionalViewSet

router = DefaultRouter()
router.register(r'periodos-vacacionales', PeriodoVacacionalViewSet, basename='periodovacional')

urlpatterns = router.urls
