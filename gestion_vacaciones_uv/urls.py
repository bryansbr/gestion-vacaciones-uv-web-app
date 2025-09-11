from django.contrib import admin
from django.urls import path, include, reverse_lazy
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authtoken.views import obtain_auth_token

def root_redirect(request):
    if request.user.is_authenticated:
        return redirect(reverse_lazy("usuarios:dashboard"))
    return redirect(reverse_lazy("usuarios:login"))

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path('api/token/', obtain_auth_token, name='api_token_auth'),
    path("core/", include("core.urls")),
    path("usuarios/", include("usuarios.urls")),
    path('vacaciones/', include('vacaciones.urls')),
    path('api/vacaciones/', include('vacaciones.urls_api')),
    path("", root_redirect),
]

# Servir archivos estáticos en modo desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
