// Script para manejar alertas del formulario de solicitud de vacaciones
document.addEventListener('DOMContentLoaded', function() {
    window.cerrarAlerta = function(idAlerta) {
        const alerta = document.getElementById(idAlerta);
        if (alerta) {
            alerta.style.display = 'none';
        }
    };

    const modalSinPeriodos = document.getElementById('modal-alerta-sin-periodos');
    const cerrarModalSinPeriodos = document.getElementById('cerrar-modal-sin-periodos');
    
    if (modalSinPeriodos && cerrarModalSinPeriodos) {
        cerrarModalSinPeriodos.addEventListener('click', function() {
            modalSinPeriodos.style.display = 'none';
        });
        
        modalSinPeriodos.addEventListener('click', function(e) {
            if (e.target === modalSinPeriodos) {
                modalSinPeriodos.style.display = 'none';
            }
        });
    }

    const modalSolicitudActiva = document.getElementById('modal-alerta-solicitud-activa');
    const cerrarModalSolicitudActiva = document.getElementById('cerrar-modal-solicitud-activa');
    
    if (modalSolicitudActiva && cerrarModalSolicitudActiva) {
        cerrarModalSolicitudActiva.addEventListener('click', function() {
            modalSolicitudActiva.style.display = 'none';
        });
        
        modalSolicitudActiva.addEventListener('click', function(e) {
            if (e.target === modalSolicitudActiva) {
                modalSolicitudActiva.style.display = 'none';
            }
        });
    }

    const modalPeriodos = document.getElementById('modal-alerta-periodos');
    const cerrarModalPeriodos = document.getElementById('cerrar-modal-periodos');
    
    if (modalPeriodos && cerrarModalPeriodos) {
        cerrarModalPeriodos.addEventListener('click', function() {
            modalPeriodos.style.display = 'none';
        });
        
        modalPeriodos.addEventListener('click', function(e) {
            if (e.target === modalPeriodos) {
                modalPeriodos.style.display = 'none';
            }
        });
    }
});
