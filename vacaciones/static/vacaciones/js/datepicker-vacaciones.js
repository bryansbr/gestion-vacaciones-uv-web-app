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
    
    // Función para mostrar mensaje de error
    function mostrarMensajeError(campoId, mensaje) {
        const campo = document.getElementById(campoId);
        if (!campo) return;
        
        // Remover mensaje anterior si existe
        const mensajeAnterior = campo.parentNode.querySelector('.mensaje-error');
        if (mensajeAnterior) {
            mensajeAnterior.remove();
        }
        
        // Crear nuevo mensaje de error
        const mensajeError = document.createElement('p');
        mensajeError.className = 'mensaje-error text-sm text-red-600 mt-1';
        mensajeError.textContent = mensaje;
        
        // Insertar después del campo
        campo.parentNode.appendChild(mensajeError);
        
        // Agregar clase de error al campo
        campo.classList.add('border-red-500');
        campo.classList.remove('border-gray-300');
    }
    
    // Función para remover mensaje de error
    function removerMensajeError(campoId) {
        const campo = document.getElementById(campoId);
        if (!campo) return;
        
        const mensajeError = campo.parentNode.querySelector('.mensaje-error');
        if (mensajeError) {
            mensajeError.remove();
        }
        
        // Remover clase de error del campo
        campo.classList.remove('border-red-500');
        campo.classList.add('border-gray-300');
    }
    
    // Función para validar fecha de inicio
    function validarFechaInicio(fecha) {
        if (esFinDeSemana(fecha)) {
            mostrarMensajeError('id_fecha_inicio_vacaciones', 'La fecha de inicio debe ser un día hábil (no puede ser fin de semana ni festivo).');
            return false;
        }
        
        if (esFestivo(fecha)) {
            mostrarMensajeError('id_fecha_inicio_vacaciones', 'La fecha de inicio debe ser un día hábil (no puede ser fin de semana ni festivo).');
            return false;
        }
        
        removerMensajeError('id_fecha_inicio_vacaciones');
        return true;
    }
    
    // Función para validar fecha de fin
    function validarFechaFin(fecha) {
        if (esFinDeSemana(fecha)) {
            mostrarMensajeError('id_fecha_fin_vacaciones', 'La fecha de fin debe ser un día hábil (no puede ser fin de semana ni festivo).');
            return false;
        }
        
        if (esFestivo(fecha)) {
            mostrarMensajeError('id_fecha_fin_vacaciones', 'La fecha de fin debe ser un día hábil (no puede ser fin de semana ni festivo).');
            return false;
        }
        
        removerMensajeError('id_fecha_fin_vacaciones');
        return true;
    }
    
    // Función para validar si todos los campos están completos
    function validarFormularioCompleto() {
        const camposRequeridos = [
            'id_periodo_vacacional',
            'id_fecha_inicio_vacaciones',
            'id_fecha_fin_vacaciones'
        ];
        
        let todosCompletos = true;
        
        camposRequeridos.forEach(campoId => {
            const campo = document.getElementById(campoId);
            if (!campo || !campo.value || campo.value.trim() === '') {
                todosCompletos = false;
            }
        });
        
        return todosCompletos;
    }
    
    // Función para validar si no hay errores de validación
    function validarSinErrores() {
        const mensajesError = document.querySelectorAll('.mensaje-error');
        return mensajesError.length === 0;
    }
    
    // Función para habilitar/deshabilitar el botón de envío
    function actualizarEstadoBoton() {
        const botonSubmit = document.getElementById('submit-btn');
        if (!botonSubmit) return;
        
        const formularioCompleto = validarFormularioCompleto();
        const sinErrores = validarSinErrores();
        
        if (formularioCompleto && sinErrores) {
            botonSubmit.disabled = false;
            botonSubmit.classList.remove('bg-gray-400', 'cursor-not-allowed');
            botonSubmit.classList.add('bg-gradient-to-r', 'from-purple-500', 'to-blue-500', 'hover:from-purple-600', 'hover:to-blue-600');
        } else {
            botonSubmit.disabled = true;
            botonSubmit.classList.add('bg-gray-400', 'cursor-not-allowed');
            botonSubmit.classList.remove('bg-gradient-to-r', 'from-purple-500', 'to-blue-500', 'hover:from-purple-600', 'hover:to-blue-600');
        }
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
                    
                    // Validar fecha de inicio
                    const fechaValida = validarFechaInicio(fecha);
                    
                    if (fechaValida) {
                        // Calcular automáticamente la fecha de fin
                        const fechaFin = calcularFechaFinAutomatica(fecha);
                        const fechaFinInput = document.getElementById('id_fecha_fin_vacaciones');
                        
                        if (fechaFinInput && fechaFinInput._flatpickr) {
                            // Formatear fecha para mostrar en dd/mm/yyyy
                            const anioFin = fechaFin.getFullYear();
                            const mesFin = String(fechaFin.getMonth() + 1).padStart(2, '0');
                            const diaFin = String(fechaFin.getDate()).padStart(2, '0');
                            
                            // Establecer la fecha en el campo de fin
                            fechaFinInput._flatpickr.setDate(fechaFin, false);
                            fechaFinInput.setAttribute('data-django-format', `${anioFin}-${mesFin}-${diaFin}`);
                        }
                    }
                    
                    // Actualizar estado del botón
                    actualizarEstadoBoton();
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
                    
                    // Validar fecha de fin
                    validarFechaFin(fecha);
                    
                    // Actualizar estado del botón
                    actualizarEstadoBoton();
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
        
        // Agregar event listeners para validación en tiempo real
        const periodoVacacional = document.getElementById('id_periodo_vacacional');
        if (periodoVacacional) {
            periodoVacacional.addEventListener('change', actualizarEstadoBoton);
        }
        
        // Inicializar estado del botón al cargar
        actualizarEstadoBoton();
    }
    
    // Función de inicialización sin validación de festivos (fallback)
    function initFlatpickrSinValidacion() {
        const fechaInicio = document.getElementById('id_fecha_inicio_vacaciones');
        const fechaFin = document.getElementById('id_fecha_fin_vacaciones');
        
        if (fechaInicio) {
            fechaInicio.removeAttribute('type');
            
            const configInicio = {
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
                },
                onChange: function(selectedDates, dateStr, instance) {
                    if (selectedDates.length > 0) {
                        const fecha = selectedDates[0];
                        const anio = fecha.getFullYear();
                        const mes = String(fecha.getMonth() + 1).padStart(2, '0');
                        const dia = String(fecha.getDate()).padStart(2, '0');
                        instance.input.setAttribute('data-django-format', `${anio}-${mes}-${dia}`);
                    }
                    actualizarEstadoBoton();
                }
            };
            
            if (fechaInicio._flatpickr) {
                fechaInicio._flatpickr.destroy();
            }
            
            try {
                flatpickr(fechaInicio, configInicio);
            } catch (error) {
                // Fallback silencioso
            }
        }
        
        if (fechaFin) {
            fechaFin.removeAttribute('type');
            
            const configFin = {
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
                },
                onChange: function(selectedDates, dateStr, instance) {
                    if (selectedDates.length > 0) {
                        const fecha = selectedDates[0];
                        const anio = fecha.getFullYear();
                        const mes = String(fecha.getMonth() + 1).padStart(2, '0');
                        const dia = String(fecha.getDate()).padStart(2, '0');
                        instance.input.setAttribute('data-django-format', `${anio}-${mes}-${dia}`);
                    }
                    actualizarEstadoBoton();
                }
            };
            
            if (fechaFin._flatpickr) {
                fechaFin._flatpickr.destroy();
            }
            
            try {
                flatpickr(fechaFin, configFin);
            } catch (error) {
                // Fallback silencioso
            }
        }
        
        // Agregar event listeners para validación del botón
        const periodoVacacional = document.getElementById('id_periodo_vacacional');
        if (periodoVacacional) {
            periodoVacacional.addEventListener('change', actualizarEstadoBoton);
        }
        
        actualizarEstadoBoton();
    }
    
    // Función para esperar a que las variables estén disponibles
    function esperarVariablesYInicializar() {
        // Función para verificar si las variables están disponibles
        function verificarVariables() {
            const festivosDisponibles = window.FESTIVOS_COLOMBIA && Array.isArray(window.FESTIVOS_COLOMBIA);
            const estamentoDisponible = window.FUNCIONARIO_ESTAMENTO !== undefined;
            
            return festivosDisponibles && estamentoDisponible;
        }
        
        // Escuchar el evento personalizado de variables listas
        document.addEventListener('variablesGlobalesListas', function() {
            if (verificarVariables()) {
                waitForFlatpickr(initFlatpickr);
            }
        });
        
        // También usar timeout como fallback con verificación más robusta
        setTimeout(function() {
            if (verificarVariables()) {
                waitForFlatpickr(initFlatpickr);
            } else {
                // Si no están disponibles después de 1 segundo, intentar de nuevo
                setTimeout(function() {
                    if (verificarVariables()) {
                        waitForFlatpickr(initFlatpickr);
                    } else {
                        // Como último recurso, inicializar sin validación de festivos
                        console.warn('Variables globales no disponibles, inicializando sin validación de festivos');
                        waitForFlatpickr(initFlatpickrSinValidacion);
                    }
                }, 1000);
            }
        }, 500);
    }
    
    // Inicializar cuando el DOM esté listo
    ready(function() {
        esperarVariablesYInicializar();
    });
    
})();
