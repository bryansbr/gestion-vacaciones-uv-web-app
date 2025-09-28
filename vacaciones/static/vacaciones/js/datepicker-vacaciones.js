// Script limpio para Flatpickr con lógica de días hábiles y festivos
(function() {
    'use strict';
    
    // Función para esperar a que el DOM esté listo
    function ready(fn) {
        if (document.readyState !== 'loading') {
            fn();
        } else {
            document.addEventListener('DOMContentLoaded', fn);
        }
    }
    
    // Función para esperar a que Flatpickr esté disponible
    function waitForFlatpickr(callback, maxAttempts = 50) {
        let attempts = 0;
        
        function check() {
            attempts++;
            
            if (typeof flatpickr !== 'undefined') {
                callback();
            } else if (attempts < maxAttempts) {
                setTimeout(check, 100);
            }
        }
        
        check();
    }
    
    // Función para verificar si una fecha es festivo
    function esFestivo(fecha) {
        const festivosColombia = window.FESTIVOS_COLOMBIA || [];
        const dia = String(fecha.getDate()).padStart(2, '0');
        const mes = String(fecha.getMonth() + 1).padStart(2, '0');
        const anio = fecha.getFullYear();
        const fechaFormatoFestivo = `${dia}/${mes}/${anio}`;
        
        return festivosColombia.includes(fechaFormatoFestivo);
    }
    
    // Función para verificar si una fecha es fin de semana
    function esFinDeSemana(fecha) {
        const diaSemana = fecha.getDay();
        return diaSemana === 0 || diaSemana === 6; // Domingo = 0, Sábado = 6
    }
    
    // Función para obtener el siguiente día hábil
    function obtenerSiguienteDiaHabil(fecha) {
        let siguienteDia = new Date(fecha);
        
        while (esFinDeSemana(siguienteDia) || esFestivo(siguienteDia)) {
            siguienteDia.setDate(siguienteDia.getDate() + 1);
        }
        
        return siguienteDia;
    }
    
    // Función para calcular la fecha de fin automáticamente
    function calcularFechaFinAutomatica(fechaInicio) {
        const estamento = (window.FUNCIONARIO_ESTAMENTO || '').toLowerCase();
        const decreto = (window.FUNCIONARIO_DECRETO || '').trim();
        
        if (estamento === 'docente') {
            if (decreto === '1279') {
                // Docente decreto 1279: 15 días hábiles + 15 días calendario = 30 días total
                let fechaFin = new Date(fechaInicio);
                let diasHabilesContados = 0;
                let diasCalendarioContados = 0;
                
                // Contar 15 días hábiles primero
                while (diasHabilesContados < 15) {
                    if (!esFinDeSemana(fechaFin) && !esFestivo(fechaFin)) {
                        diasHabilesContados++;
                    }
                    fechaFin.setDate(fechaFin.getDate() + 1);
                }
                
                // Luego agregar 15 días calendario
                fechaFin.setDate(fechaFin.getDate() + 15);
                
                return fechaFin;
            } else if (decreto === '115') {
                // Docente decreto 115: 30 días calendario
                let fechaFin = new Date(fechaInicio);
                fechaFin.setDate(fechaFin.getDate() + 30);
                return fechaFin;
            }
        } else if (estamento === 'administrativo') {
            // Administrativo: 15 días hábiles
            let fechaFin = new Date(fechaInicio);
            let diasHabilesContados = 0;
            
            while (diasHabilesContados < 15) {
                if (!esFinDeSemana(fechaFin) && !esFestivo(fechaFin)) {
                    diasHabilesContados++;
                }
                fechaFin.setDate(fechaFin.getDate() + 1);
            }
            
            return fechaFin;
        } else if (estamento === 'trabajador oficial') {
            // Trabajador oficial: 30 días calendario
            let fechaFin = new Date(fechaInicio);
            fechaFin.setDate(fechaFin.getDate() + 30);
            return fechaFin;
        }
        
        // Fallback: 15 días calendario
        let fechaFin = new Date(fechaInicio);
        fechaFin.setDate(fechaFin.getDate() + 15);
        return fechaFin;
    }
    
    // Función para calcular la fecha mínima de inicio según el estamento
    function calcularFechaMinimaInicio() {
        const hoy = new Date();
        hoy.setHours(0, 0, 0, 0);
        
        const disfruteDiasPendientes = document.getElementById('id_tiene_dias_pendientes');
        const esDisfrutePendientes = disfruteDiasPendientes && disfruteDiasPendientes.checked;
        
        if (esDisfrutePendientes) {
            const fechaMinima = new Date(hoy);
            fechaMinima.setDate(hoy.getDate() + 1);
            return obtenerSiguienteDiaHabil(fechaMinima);
        } else {
            const estamento = (window.FUNCIONARIO_ESTAMENTO || '').toLowerCase();
            let fechaSalida = new Date();
            
            if (estamento === 'docente') {
                if (hoy.getDate() <= 10) {
                    if (hoy.getMonth() === 11) {
                        fechaSalida = new Date(hoy.getFullYear() + 1, 0, 1);
                    } else {
                        fechaSalida = new Date(hoy.getFullYear(), hoy.getMonth() + 1, 1);
                    }
                } else {
                    if (hoy.getMonth() === 11) {
                        fechaSalida = new Date(hoy.getFullYear() + 1, 1, 1);
                    } else if (hoy.getMonth() === 10) {
                        fechaSalida = new Date(hoy.getFullYear() + 1, 0, 1);
                    } else {
                        fechaSalida = new Date(hoy.getFullYear(), hoy.getMonth() + 2, 1);
                    }
                }
            } else {
                if (hoy.getDate() <= 3) {
                    fechaSalida = new Date(hoy.getFullYear(), hoy.getMonth(), 16);
                } else if (hoy.getDate() <= 17) {
                    if (hoy.getMonth() === 11) {
                        fechaSalida = new Date(hoy.getFullYear() + 1, 0, 1);
                    } else {
                        fechaSalida = new Date(hoy.getFullYear(), hoy.getMonth() + 1, 1);
                    }
                } else {
                    if (hoy.getMonth() === 11) {
                        fechaSalida = new Date(hoy.getFullYear() + 1, 0, 16);
                    } else {
                        fechaSalida = new Date(hoy.getFullYear(), hoy.getMonth() + 1, 16);
                    }
                }
            }
            
            return obtenerSiguienteDiaHabil(fechaSalida);
        }
    }
    
    // Función principal de inicialización
    function initFlatpickr() {
        const fechaMinimaInicio = calcularFechaMinimaInicio();
        
        // Configuración base de Flatpickr
        const configBase = {
            dateFormat: "d/m/Y",
            allowInput: true,
            locale: {
                firstDayOfWeek: 1,
                weekdays: {
                    shorthand: ["Do", "Lu", "Ma", "Mi", "Ju", "Vi", "Sa"],
                    longhand: ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"],
                },
                months: {
                    shorthand: ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
                    longhand: ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"],
                },
            }
        };
        
        // Configuración específica para fecha de inicio
        const configInicio = {
            ...configBase,
            minDate: fechaMinimaInicio,
            disable: [
                function(date) {
                    const esFinSemana = esFinDeSemana(date);
                    const esFestivoFecha = esFestivo(date);
                    const esMenorQueMinima = date < fechaMinimaInicio;
                    
                    return esFinSemana || esFestivoFecha || esMenorQueMinima;
                }
            ],
            onChange: function(selectedDates, dateStr, instance) {
                if (selectedDates.length > 0) {
                    const fecha = selectedDates[0];
                    const anio = fecha.getFullYear();
                    const mes = String(fecha.getMonth() + 1).padStart(2, '0');
                    const dia = String(fecha.getDate()).padStart(2, '0');
                    instance.input.setAttribute('data-django-format', `${anio}-${mes}-${dia}`);
                    
                    // Calcular automáticamente la fecha de fin
                    const fechaFin = calcularFechaFinAutomatica(fecha);
                    const fechaFinInput = document.getElementById('id_fecha_fin_vacaciones');
                    
                    if (fechaFinInput && fechaFinInput._flatpickr) {
                        // Formatear fecha para mostrar en dd/mm/yyyy
                        const anioFin = fechaFin.getFullYear();
                        const mesFin = String(fechaFin.getMonth() + 1).padStart(2, '0');
                        const diaFin = String(fechaFin.getDate()).padStart(2, '0');
                        const fechaFinFormateada = `${diaFin}/${mesFin}/${anioFin}`;
                        
                        // Establecer la fecha en el campo de fin
                        fechaFinInput._flatpickr.setDate(fechaFin, false);
                        fechaFinInput.setAttribute('data-django-format', `${anioFin}-${mesFin}-${diaFin}`);
                    }
                }
            }
        };
        
        // Configuración específica para fecha de fin
        const configFin = {
            ...configBase,
            disable: [
                function(date) {
                    const esFinSemana = esFinDeSemana(date);
                    const esFestivoFecha = esFestivo(date);
                    
                    return esFinSemana || esFestivoFecha;
                }
            ],
            onChange: function(selectedDates, dateStr, instance) {
                if (selectedDates.length > 0) {
                    const fecha = selectedDates[0];
                    const anio = fecha.getFullYear();
                    const mes = String(fecha.getMonth() + 1).padStart(2, '0');
                    const dia = String(fecha.getDate()).padStart(2, '0');
                    instance.input.setAttribute('data-django-format', `${anio}-${mes}-${dia}`);
                }
            }
        };
        
        // Configurar campo de fecha de inicio
        const fechaInicio = document.getElementById('id_fecha_inicio_vacaciones');
        if (fechaInicio) {
            fechaInicio.removeAttribute('type');
            
            if (fechaInicio._flatpickr) {
                fechaInicio._flatpickr.destroy();
            }
            
            try {
                flatpickr(fechaInicio, configInicio);
                fechaInicio.classList.add('input-fecha');
            } catch (error) {
                // Fallback silencioso
            }
        }
        
        // Configurar campo de fecha de fin
        const fechaFin = document.getElementById('id_fecha_fin_vacaciones');
        if (fechaFin) {
            fechaFin.removeAttribute('type');
            
            if (fechaFin._flatpickr) {
                fechaFin._flatpickr.destroy();
            }
            
            try {
                flatpickr(fechaFin, configFin);
                fechaFin.classList.add('input-fecha');
            } catch (error) {
                // Fallback silencioso
            }
        }
        
        // Configurar conversión de formato al enviar formulario
        const form = document.querySelector('form');
        if (form) {
            form.addEventListener('submit', function(e) {
                [fechaInicio, fechaFin].forEach((input) => {
                    if (input && input.value) {
                        if (input.value.match(/^\d{2}\/\d{2}\/\d{4}$/)) {
                            const partes = input.value.split('/');
                            const dia = partes[0];
                            const mes = partes[1];
                            const anio = partes[2];
                            input.value = `${anio}-${mes}-${dia}`;
                        }
                    }
                });
            });
        }
    }
    
    // Función para esperar a que las variables estén disponibles
    function esperarVariablesYInicializar() {
        // Escuchar el evento personalizado de variables listas
        document.addEventListener('variablesGlobalesListas', function() {
            waitForFlatpickr(initFlatpickr);
        });
        
        // También usar timeout como fallback
        setTimeout(function() {
            if (window.VARIABLES_GLOBALES_LISTAS) {
                waitForFlatpickr(initFlatpickr);
            } else {
                // Si no están disponibles después de 2 segundos, inicializar de todas formas
                setTimeout(function() {
                    waitForFlatpickr(initFlatpickr);
                }, 2000);
            }
        }, 500);
    }
    
    // Inicializar cuando el DOM esté listo
    ready(function() {
        esperarVariablesYInicializar();
    });
    
})();
