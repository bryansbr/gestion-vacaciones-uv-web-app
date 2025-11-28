"""
Vistas para el módulo de Estado de Vacaciones.
Proporciona un panel informativo sobre el estado de vacaciones del funcionario.
"""
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from usuarios.models import Funcionario
from vacaciones.services.estado_vacaciones import obtener_estado_completo_vacaciones

class EstadoVacacionesView(LoginRequiredMixin, TemplateView):
    """
    Vista principal del módulo de Estado de Vacaciones.
    
    Muestra información consolidada sobre:
    - Resumen vacacional (días asignados, disfrutados, pendientes)
    - Listado de periodos vacacionales
    - Historial de solicitudes y reintegros
    - Datos del régimen del funcionario
    
    Acceso: Todos los usuarios autenticados pueden ver su propio estado.
    """
    template_name = 'vacaciones/estado/estado-vacaciones.html'
    
    def dispatch(self, request, *args, **kwargs):
        """Verifica que el usuario tenga un funcionario asociado."""
        user = request.user
        
        if not hasattr(user, 'funcionario'):
            raise PermissionDenied("No tiene un funcionario asociado.")
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        funcionario = user.funcionario
        estado_completo = obtener_estado_completo_vacaciones(funcionario)
        
        context.update({
            'estado_vacaciones': estado_completo,
            'funcionario': funcionario,
        })
        
        return context
