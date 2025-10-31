(function() {
    'use strict';
    
    function configurarVariablesGlobales() {
        const container = document.getElementById('variables-container') || document.querySelector('div[data-funcionario-estamento]');
        
        if (container) {
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
            
            window.FUNCIONARIO_ESTAMENTO = container.getAttribute('data-funcionario-estamento') || '';
            window.FUNCIONARIO_DECRETO = container.getAttribute('data-funcionario-decreto') || '';
            
            if (container.hasAttribute('data-reintegros-pendientes')) {
                try {
                    window.REINTEGROS_PENDIENTES = JSON.parse(container.getAttribute('data-reintegros-pendientes'));
                } catch (e) {
                    window.REINTEGROS_PENDIENTES = [];
                }
            } else {
                window.REINTEGROS_PENDIENTES = [];
            }
            
            if (container.hasAttribute('data-periodos-dias-pendientes')) {
                try {
                    window.PERIODOS_DIAS_PENDIENTES = JSON.parse(container.getAttribute('data-periodos-dias-pendientes'));
                } catch (e) {
                    window.PERIODOS_DIAS_PENDIENTES = {};
                }
            } else {
                window.PERIODOS_DIAS_PENDIENTES = {};
            }
            
            window.VARIABLES_GLOBALES_LISTAS = true;
            
            const event = new CustomEvent('variablesGlobalesListas');
            document.dispatchEvent(event);
            
            return true;
        } else {
            window.FESTIVOS_COLOMBIA = [];
            window.FUNCIONARIO_ESTAMENTO = '';
            window.FUNCIONARIO_DECRETO = '';
            window.REINTEGROS_PENDIENTES = [];
            window.PERIODOS_DIAS_PENDIENTES = {};
            window.VARIABLES_GLOBALES_LISTAS = true;
            
            const event = new CustomEvent('variablesGlobalesListas');
            document.dispatchEvent(event);
            
            return false;
        }
    }
    
    function ready(fn) {
        if (document.readyState !== 'loading') {
            fn();
        } else {
            document.addEventListener('DOMContentLoaded', fn);
        }
    }
    
    ready(function() {
        if (!configurarVariablesGlobales()) {
            setTimeout(configurarVariablesGlobales, 100);
            setTimeout(configurarVariablesGlobales, 500);
            setTimeout(configurarVariablesGlobales, 1000);
        }
    });
})();
