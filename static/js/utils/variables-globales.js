// Script para configurar variables globales desde Django
document.addEventListener('DOMContentLoaded', function() {
    // Obtener variables desde atributos de datos del div contenedor
    const container = document.querySelector('div[data-funcionario-estamento]');
    
    if (container) {
        // Configurar festivos de Colombia
        if (container.hasAttribute('data-festivos-colombia')) {
            try {
                window.FESTIVOS_COLOMBIA = JSON.parse(container.getAttribute('data-festivos-colombia'));
            } catch (e) {
                window.FESTIVOS_COLOMBIA = [];
            }
        } else {
            window.FESTIVOS_COLOMBIA = [];
        }
        
        // Configurar variables del funcionario
        window.FUNCIONARIO_ESTAMENTO = container.getAttribute('data-funcionario-estamento') || '';
        window.FUNCIONARIO_DECRETO = container.getAttribute('data-funcionario-decreto') || '';
        
        // Configurar reintegros pendientes
        if (container.hasAttribute('data-reintegros-pendientes')) {
            try {
                window.REINTEGROS_PENDIENTES = JSON.parse(container.getAttribute('data-reintegros-pendientes'));
            } catch (e) {
                window.REINTEGROS_PENDIENTES = [];
            }
        } else {
            window.REINTEGROS_PENDIENTES = [];
        }
    } else {
        // Valores por defecto si no se encuentra el contenedor
        window.FESTIVOS_COLOMBIA = [];
        window.FUNCIONARIO_ESTAMENTO = '';
        window.FUNCIONARIO_DECRETO = '';
        window.REINTEGROS_PENDIENTES = [];
    }
}); 