from django.contrib import admin
from django.urls import path, include, reverse_lazy
from django.shortcuts import redirect
from django.contrib.auth.views import LogoutView

def root_redirect(request):
    if request.user.is_authenticated:
        return redirect(reverse_lazy("usuarios:dashboard"))
    return redirect(reverse_lazy("usuarios:login"))

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("core/", include("core.urls")),
    path("usuarios/", include("usuarios.urls")),
    path("logout/", LogoutView.as_view(next_page='usuarios:login'), name='logout'),
    path("", root_redirect),
]
