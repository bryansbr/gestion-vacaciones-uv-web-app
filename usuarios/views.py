from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from .forms import CustomAuthenticationForm

class CustomLoginView(LoginView):
    template_name = "login.html"
    redirect_authenticated_user = True
    authentication_form = CustomAuthenticationForm
    
    def get_success_url(self):
        return reverse_lazy("usuarios:dashboard")

@login_required
def dashboard(request):
    return render(request, "home.html")

def custom_logout(request):
    """
    Vista personalizada para cerrar sesión y redirigir a la página de inicio de sesión.
    """
    # Cerrar sesión explícitamente
    logout(request)
    
    # Redirigir a la página de inicio de sesión
    return redirect('usuarios:login')
