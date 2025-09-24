// Script para configurar variables globales desde Django
document.addEventListener('DOMContentLoaded', function() {
    // Función para configurar variables globales
    function configurarVariablesGlobales() {
        // Obtener variables desde atributos de datos del div contenedor
        const container = document.querySelector('div[data-funcionario-estamento]');
        
        if (container) {
            // Configurar festivos de Colombia
            if (container.hasAttribute('data-festivos-colombia')) {
                const festivosAttr = container.getAttribute('data-festivos-colombia');
                if (festivosAttr && festivosAttr.trim() !== '' && festivosAttr !== '[]') {
                    try {
                        window.FESTIVOS_COLOMBIA = JSON.parse(festivosAttr);
                    } catch (e) {
                        window.FESTIVOS_COLOMBIA = [];
                    }
                } else {
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
                    console.warn('Error parseando reintegros pendientes:', e);
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
        
        // Marcar que las variables están listas
        window.VARIABLES_GLOBALES_LISTAS = true;
        
        // Disparar evento personalizado para notificar que las variables están listas
        const event = new CustomEvent('variablesGlobalesListas');
        document.dispatchEvent(event);
    }
    
    // Configurar inmediatamente
    configurarVariablesGlobales();
    
    // También configurar después de un pequeño delay por si acaso
    setTimeout(configurarVariablesGlobales, 100);
}); 