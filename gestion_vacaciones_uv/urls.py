from django.contrib import admin
from django.urls import path, include, reverse_lazy
from django.shortcuts import redirect

urlpatterns = [
    path("admin/", admin.site.urls),
    path("usuarios/", include("usuarios.urls")),
    path("core/", include("core.urls")),
    path("", lambda request: redirect(reverse_lazy("login"))),
]
