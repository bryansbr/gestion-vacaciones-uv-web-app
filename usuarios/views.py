from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
import calendar
from .forms import CustomAuthenticationForm
from .services import obtener_datos_dashboard
from core.permissions import (
    es_secretaria,
    es_jefe_inmediato,
    es_coordinador_administrativo,
    es_rrhh
)

from vacaciones.utils import get_current_date_colombia

class CustomLoginView(LoginView):
    template_name = "usuarios/iniciar-sesion.html"
    redirect_authenticated_user = True
    authentication_form = CustomAuthenticationForm

    def get_success_url(self):
        return reverse_lazy("usuarios:dashboard")

@login_required
def dashboard(request):
    """
    Vista del dashboard que muestra widgets según el rol del usuario.
    """
    datos = obtener_datos_dashboard(request.user)
    
    rol = 'funcionario'
    if es_rrhh(request.user):
        rol = 'rrhh'
    elif es_secretaria(request.user):
        rol = 'secretaria'
    elif es_coordinador_administrativo(request.user):
        rol = 'coordinador'
    elif es_jefe_inmediato(request.user):
        rol = 'jefe'
    
    hoy = get_current_date_colombia()
    mes_actual = hoy.month
    año_actual = hoy.year
    dia_actual = hoy.day
    
    cal = calendar.monthcalendar(año_actual, mes_actual)
    
    meses_es = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    
    mes_nombre = meses_es[mes_actual]
    
    context = {
        'datos': datos or {},
        'rol': rol,
        'calendario': cal,
        'mes_nombre': mes_nombre,
        'año': año_actual,
        'dia_actual': dia_actual,
        'mes_actual': mes_actual,
    }
    
    return render(request, "home.html", context)

def custom_logout(request):
    logout(request)
    return redirect('usuarios:login')
