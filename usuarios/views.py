from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views import View
from django.contrib import messages

class CustomLoginView(LoginView):
    template_name = "login.html"
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy("usuarios:dashboard")
    
    def form_valid(self, form):
        email = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(self.request, username=email, password=password)
        
        if user is not None:
            login(self.request, user)
            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)

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
