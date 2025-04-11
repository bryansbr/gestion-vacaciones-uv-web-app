from django.contrib import admin
from django.urls import path, include, reverse_lazy
from django.shortcuts import redirect

def root_redirect(request):
    if request.user.is_authenticated:
        return redirect(reverse_lazy("usuarios:dashboard"))
    return redirect(reverse_lazy("login"))

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("core/", include("core.urls")),
    path("usuarios/", include("usuarios.urls")),
    path("", root_redirect),
]
