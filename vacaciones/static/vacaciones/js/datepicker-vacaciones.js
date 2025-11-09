(function() {
    'use strict';
    
    function ready(fn) {
        if (document.readyState !== 'loading') fn();
        else document.addEventListener('DOMContentLoaded', fn);
    }

    // ----------------- Error Handling -----------------
    function handleFlatpickrError(error, elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'flatpickr-error text-sm text-red-600 mt-1';
            errorDiv.textContent = 'Error al inicializar el selector de fechas. Por favor, recargue la página.';
            element.parentNode.insertBefore(errorDiv, element.nextSibling);
            element.style.borderColor = '#ef4444';
        }
        
        if (element) {
            element.type = 'text';
            element.placeholder = 'dd/mm/aaaa';
            element.classList.add('input-fecha-fallback');
        }
    }

    function esperarFlatpickr(callback, maxAttempts = 20, intervalMs = 100) {
        let attempts = 0;
        (function check() {
            attempts++;
            if (typeof flatpickr !== 'undefined') {
                callback();
            } else if (attempts < maxAttempts) {
                setTimeout(check, intervalMs);
            } else {
                mostrarErrorFlatpickrNoDisponible();
            }
        })();
    }

    // ----------------- Constantes de configuración -----------------
    const ERROR_CONFIG = {
        title: 'Advertencia de inicialización',
        message: 'El selector de fechas no se pudo inicializar correctamente. Los campos de fecha funcionarán como campos de texto básicos.',
        iconPath: 'M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z',
        classes: {
            container: 'flatpickr-timeout-error bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded mb-4',
            icon: 'h-5 w-5 text-yellow-400',
            title: 'text-sm font-medium',
            message: 'mt-2 text-sm'
        }
    };

    const FALLBACK_CONFIG = {
        placeholder: 'dd/mm/aaaa',
        fallbackClass: 'input-fecha-fallback',
        selectors: ['input[type="date"]', '.flatpickr-input']
    };

    // ----------------- Utilidades de creación de elementos -----------------
    function crearIconoSVG(path, className) {
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('class', className);
        svg.setAttribute('viewBox', '0 0 20 20');
        svg.setAttribute('fill', 'currentColor');
        
        const pathElement = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        pathElement.setAttribute('fill-rule', 'evenodd');
        pathElement.setAttribute('d', path);
        pathElement.setAttribute('clip-rule', 'evenodd');
        
        svg.appendChild(pathElement);
        return svg;
    }

    function crearElementoConClases(tagName, className) {
        const elemento = document.createElement(tagName);
        if (className) {
            elemento.className = className;
        }
        return elemento;
    }

    function crearTextoElemento(tagName, texto, className) {
        const elemento = crearElementoConClases(tagName, className);
        elemento.textContent = texto;
        return elemento;
    }

    // ----------------- Creación de componentes -----------------
    function crearComponenteIcono() {
        const iconContainer = crearElementoConClases('div', 'flex-shrink-0');
        const icono = crearIconoSVG(ERROR_CONFIG.iconPath, ERROR_CONFIG.classes.icon);
        iconContainer.appendChild(icono);
        return iconContainer;
    }

    function crearComponenteContenido() {
        const contentContainer = crearElementoConClases('div', 'ml-3');
        
        const titulo = crearTextoElemento('h3', ERROR_CONFIG.title, ERROR_CONFIG.classes.title);
        const mensajeContainer = crearElementoConClases('div', ERROR_CONFIG.classes.message);
        const mensaje = crearTextoElemento('p', ERROR_CONFIG.message);
        
        mensajeContainer.appendChild(mensaje);
        contentContainer.appendChild(titulo);
        contentContainer.appendChild(mensajeContainer);
        
        return contentContainer;
    }

    function crearBannerError() {
        const banner = crearElementoConClases('div', ERROR_CONFIG.classes.container);
        const flexContainer = crearElementoConClases('div', 'flex');
        
        flexContainer.appendChild(crearComponenteIcono());
        flexContainer.appendChild(crearComponenteContenido());
        banner.appendChild(flexContainer);
        
        return banner;
    }

    // ----------------- Utilidades de inserción -----------------
    function insertarBannerEnFormulario(banner) {
        const form = document.querySelector('form');
        if (form) {
            form.insertBefore(banner, form.firstChild);
        } else {
            document.body.insertBefore(banner, document.body.firstChild);
        }
    }

    function convertirCamposAFallback() {
        const selectores = FALLBACK_CONFIG.selectors.join(', ');
        const camposFecha = document.querySelectorAll(selectores);
        
        camposFecha.forEach(campo => {
            campo.type = 'text';
            campo.placeholder = FALLBACK_CONFIG.placeholder;
            campo.classList.add(FALLBACK_CONFIG.fallbackClass);
        });
    }

    // ----------------- Función principal -----------------
    function mostrarErrorFlatpickrNoDisponible() {
        const banner = crearBannerError();
        insertarBannerEnFormulario(banner);
        convertirCamposAFallback();
    }

    // ----------------- Fechas y Festivos -----------------
    function esFestivo(fecha) {
        const festivosColombia = window.FESTIVOS_COLOMBIA || [];
        const dia = String(fecha.getDate()).padStart(2, '0');
        const mes = String(fecha.getMonth() + 1).padStart(2, '0');
        const anio = fecha.getFullYear();
        const fechaFormatoFestivo = `${dia}/${mes}/${anio}`;
        return festivosColombia.includes(fechaFormatoFestivo);
    }

    function esFinDeSemana(fecha) {
        const d = fecha.getDay();
        return d === 0 || d === 6;
    }

    function obtenerSiguienteDiaHabil(fecha) {
        let f = new Date(fecha);
        while (esFinDeSemana(f) || esFestivo(f)) {
            f.setDate(f.getDate() + 1);
        }
        return f;
    }

    function sumarDiasCalendario(fecha, n) {
        const f = new Date(fecha);
        f.setDate(f.getDate() + n);
        return f;
    }

    function sumarDiasHabiles(fecha, n) {
        let f = new Date(fecha);
        let cont = 0;
        let ultimoDiaHabil = new Date(fecha);
        if (n <= 0) {
            return ultimoDiaHabil;
        }
        while (cont < n) {
            if (!esFinDeSemana(f) && !esFestivo(f)) {
                cont++;
                ultimoDiaHabil = new Date(f);
            }
            f.setDate(f.getDate() + 1);
        }
        return ultimoDiaHabil;
    }
      
    // ----------------- Mensajes de error -----------------
    function mostrarMensajeError(campoId, mensaje) {
        const campo = document.getElementById(campoId);
        if (!campo) return;
        const prev = campo.parentNode.querySelector('.mensaje-error');
        if (prev) prev.remove();
        const p = document.createElement('p');
        p.className = 'mensaje-error text-sm text-red-600 mt-1';
        p.textContent = mensaje;
        campo.parentNode.appendChild(p);
        campo.classList.add('border-red-500');
        campo.classList.remove('border-gray-300');
    }

    function removerMensajeError(campoId) {
        const campo = document.getElementById(campoId);
        if (!campo) return;
        const prev = campo.parentNode.querySelector('.mensaje-error');
        if (prev) prev.remove();
        campo.classList.remove('border-red-500');
        campo.classList.add('border-gray-300');
    }

    function validarFechaInicio(fecha) {
        if (esFinDeSemana(fecha) || esFestivo(fecha)) {
            mostrarMensajeError('id_fecha_inicio_vacaciones', 'La fecha de inicio debe ser un día hábil (no puede ser fin de semana ni festivo).');
            return false;
        }
        removerMensajeError('id_fecha_inicio_vacaciones');
        return true;
    }

    function validarFechaFin(fecha) {
        if (esFinDeSemana(fecha) || esFestivo(fecha)) {
            mostrarMensajeError('id_fecha_fin_vacaciones', 'La fecha de fin debe ser un día hábil (no puede ser fin de semana ni festivo).');
            return false;
        }
        removerMensajeError('id_fecha_fin_vacaciones');
        return true;
    }

    function validarFormularioCompleto() {
        const campos = ['id_periodo_vacacional','id_fecha_inicio_vacaciones','id_fecha_fin_vacaciones'];
        return campos.every(id => {
            const el = document.getElementById(id);
            return el && el.value && el.value.trim() !== '';
        });
    }

    function validarSinErrores() {
        return document.querySelectorAll('.mensaje-error').length === 0;
    }

    function actualizarEstadoBoton() {
        const btn = document.getElementById('submit-btn');
        if (!btn) return;
        if (validarFormularioCompleto() && validarSinErrores()) {
            btn.disabled = false;
            btn.classList.remove('bg-gray-400','cursor-not-allowed');
            btn.classList.add('bg-gradient-to-r','from-purple-500','to-blue-500','hover:from-purple-600','hover:to-blue-600');
        } else {
            btn.disabled = true;
            btn.classList.add('bg-gray-400','cursor-not-allowed');
            btn.classList.remove('bg-gradient-to-r','from-purple-500','to-blue-500','hover:from-purple-600','hover:to-blue-600');
        }
    }

    function calcularFechaMinimaInicio() {
        const hoy = new Date();
        hoy.setHours(0,0,0,0);

        const disfruteDiasPendientes = document.getElementById('id_tiene_dias_pendientes');
        const esDisfrutePendientes = disfruteDiasPendientes && disfruteDiasPendientes.checked;

        if (esDisfrutePendientes) {
            const f = new Date(hoy);
            f.setDate(hoy.getDate() + 1);
            return obtenerSiguienteDiaHabil(f);
        } else {
            const estamento = (window.FUNCIONARIO_ESTAMENTO || '').toLowerCase();
            let fechaSalida = new Date();
            if (estamento === 'docente') {
                if (hoy.getDate() <= 10) {
                    fechaSalida = (hoy.getMonth() === 11) ? new Date(hoy.getFullYear()+1,0,1)
                                                          : new Date(hoy.getFullYear(), hoy.getMonth()+1, 1);
                } else {
                    if (hoy.getMonth() === 11) {
                        fechaSalida = new Date(hoy.getFullYear()+1, 1, 1);
                    } else if (hoy.getMonth() === 10) {
                        fechaSalida = new Date(hoy.getFullYear()+1, 0, 1);
                    } else {
                        fechaSalida = new Date(hoy.getFullYear(), hoy.getMonth()+2, 1);
                    }
                }
            } else {
                if (hoy.getDate() <= 3) {
                    fechaSalida = new Date(hoy.getFullYear(), hoy.getMonth(), 16);
                } else if (hoy.getDate() <= 17) {
                    fechaSalida = (hoy.getMonth() === 11) ? new Date(hoy.getFullYear()+1,0,1)
                                                          : new Date(hoy.getFullYear(), hoy.getMonth()+1, 1);
                } else {
                    fechaSalida = (hoy.getMonth() === 11) ? new Date(hoy.getFullYear()+1,0,16)
                                                          : new Date(hoy.getFullYear(), hoy.getMonth()+1, 16);
                }
            }
            return obtenerSiguienteDiaHabil(fechaSalida);
        }
    }

    function calcularFechaFinAutomatica(fechaInicio) {
        const estamento = (window.FUNCIONARIO_ESTAMENTO || '').toLowerCase();
        const decreto = (window.FUNCIONARIO_DECRETO || '').trim();
      
        if (estamento === 'docente') {
            if (decreto === '1279') {
              const finHabiles = sumarDiasHabiles(fechaInicio, 15);
              const f = new Date(finHabiles);
              f.setDate(f.getDate() + 15);
              return f;
            } else if (decreto === '115') {
              return sumarDiasCalendario(fechaInicio, 30);
            }
        } else if (estamento === 'administrativo') {
          return sumarDiasHabiles(fechaInicio, 15);
        } else if (estamento === 'trabajador oficial') {
          return sumarDiasCalendario(fechaInicio, 30);
        }
        return sumarDiasCalendario(fechaInicio, 15);
      }      

    // ----------------- Inicialización Flatpickr -----------------
    function inicializarFlatpickr() {
        const fechaMinimaInicio = calcularFechaMinimaInicio();

        const configBase = {
            dateFormat: "d/m/Y",
            allowInput: true,
            locale: {
                firstDayOfWeek: 1,
                weekdays: {
                    shorthand: ["Do","Lu","Ma","Mi","Ju","Vi","Sa"],
                    longhand: ["Domingo","Lunes","Martes","Miércoles","Jueves","Viernes","Sábado"],
                },
                months: {
                    shorthand: ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"],
                    longhand: ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"],
                },
            }
        };

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
                    const y = fecha.getFullYear();
                    const m = String(fecha.getMonth()+1).padStart(2,'0');
                    const d = String(fecha.getDate()).padStart(2,'0');
                    instance.input.setAttribute('data-django-format', `${y}-${m}-${d}`);

                    if (validarFechaInicio(fecha)) {
                        const fin = calcularFechaFinAutomatica(fecha);
                        const finInput = document.getElementById('id_fecha_fin_vacaciones');
                        if (finInput && finInput._flatpickr) {
                            finInput._flatpickr.setDate(fin, false);
                            const yf = fin.getFullYear();
                            const mf = String(fin.getMonth()+1).padStart(2,'0');
                            const df = String(fin.getDate()).padStart(2,'0');
                            finInput.setAttribute('data-django-format', `${yf}-${mf}-${df}`);
                        }
                    }
                    actualizarEstadoBoton();
                } else {
                    actualizarEstadoBoton();
                }
            }
        };

        const configFin = {
            ...configBase,
            disable: [
                function(date) {
                    return esFinDeSemana(date) || esFestivo(date);
                }
            ],
            onChange: function(selectedDates, dateStr, instance) {
                if (selectedDates.length > 0) {
                    const f = selectedDates[0];
                    const y = f.getFullYear();
                    const m = String(f.getMonth()+1).padStart(2,'0');
                    const d = String(f.getDate()).padStart(2,'0');
                    instance.input.setAttribute('data-django-format', `${y}-${m}-${d}`);
                    validarFechaFin(f);
                    actualizarEstadoBoton();
                } else {
                    actualizarEstadoBoton();
                }
            }
        };

        const fechaInicio = document.getElementById('id_fecha_inicio_vacaciones');
        const fechaFin    = document.getElementById('id_fecha_fin_vacaciones');

        if (fechaInicio) {
            fechaInicio.removeAttribute('type');
            if (fechaInicio._flatpickr) fechaInicio._flatpickr.destroy();
            try { 
                flatpickr(fechaInicio, configInicio); 
                fechaInicio.classList.add('input-fecha'); 
            } catch(error) {
                handleFlatpickrError(error, 'id_fecha_inicio_vacaciones');
            }
        }

        if (fechaFin) {
            fechaFin.removeAttribute('type');
            if (fechaFin._flatpickr) fechaFin._flatpickr.destroy();
            try { 
                flatpickr(fechaFin, configFin); 
                fechaFin.classList.add('input-fecha'); 
            } catch(error) {
                handleFlatpickrError(error, 'id_fecha_fin_vacaciones');
            }
        }

        function setFechaInicial(fpInput, raw) {
            if (!fpInput || !raw || !fpInput._flatpickr) return;
            const fp = fpInput._flatpickr;
            if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) {
                fp.setDate(raw, false, "Y-m-d");
            } else if (/^\d{2}\/\d{2}\/\d{4}$/.test(raw)) {
                fp.setDate(raw, false, "d/m/Y");
            }
        }

        if (fechaInicio && fechaInicio.value) setFechaInicial(fechaInicio, fechaInicio.value);
        if (fechaFin && fechaFin.value)       setFechaInicial(fechaFin,    fechaFin.value);

        if (fechaInicio && fechaInicio._flatpickr && fechaInicio.value && fechaFin && !fechaFin.value) {
            const f = fechaInicio._flatpickr.selectedDates[0];
            if (f) {
                const fin = calcularFechaFinAutomatica(f);
                fechaFin._flatpickr.setDate(fin, false);
                const yf = fin.getFullYear();
                const mf = String(fin.getMonth()+1).padStart(2,'0');
                const df = String(fin.getDate()).padStart(2,'0');
                fechaFin.setAttribute('data-django-format', `${yf}-${mf}-${df}`);
            }
        }

        // Conversión a YYYY-mm-dd
        const form = document.querySelector('form');
        if (form) {
            form.addEventListener('submit', function() {
                [fechaInicio, fechaFin].forEach((input) => {
                    if (input && input.value) {
                        if (/^\d{2}\/\d{2}\/\d{4}$/.test(input.value)) {
                            const [dd, mm, yyyy] = input.value.split('/');
                            input.value = `${yyyy}-${mm}-${dd}`;
                        }
                    }
                });
            });
        }

        const periodoVacacional = document.getElementById('id_periodo_vacacional');
        if (periodoVacacional) periodoVacacional.addEventListener('change', actualizarEstadoBoton);

        if (fechaInicio) {
            fechaInicio.addEventListener('input', actualizarEstadoBoton);
            fechaInicio.addEventListener('keyup', actualizarEstadoBoton);
        }
        if (fechaFin) {
            fechaFin.addEventListener('input', actualizarEstadoBoton);
            fechaFin.addEventListener('keyup', actualizarEstadoBoton);
        }

        actualizarEstadoBoton();
    }

    function initFlatpickrSinValidacion() {
        const fechaInicio = document.getElementById('id_fecha_inicio_vacaciones');
        const fechaFin    = document.getElementById('id_fecha_fin_vacaciones');

        const base = {
            dateFormat: "d/m/Y",
            allowInput: true,
            locale: {
                firstDayOfWeek: 1,
                weekdays: {
                    shorthand: ["Do","Lu","Ma","Mi","Ju","Vi","Sa"],
                    longhand: ["Domingo","Lunes","Martes","Miércoles","Jueves","Viernes","Sábado"],
                },
                months: {
                    shorthand: ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"],
                    longhand: ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"],
                },
            },
            onChange: function(selectedDates, dateStr, instance) {
                if (selectedDates.length > 0) {
                    const f = selectedDates[0];
                    const y = f.getFullYear();
                    const m = String(f.getMonth()+1).padStart(2,'0');
                    const d = String(f.getDate()).padStart(2,'0');
                    instance.input.setAttribute('data-django-format', `${y}-${m}-${d}`);
                }
                actualizarEstadoBoton();
            }
        };

        if (fechaInicio) {
            fechaInicio.removeAttribute('type');
            if (fechaInicio._flatpickr) fechaInicio._flatpickr.destroy();
            try { 
                flatpickr(fechaInicio, base); 
                fechaInicio.classList.add('input-fecha'); 
            } catch(error) {
                handleFlatpickrError(error, 'id_fecha_inicio_vacaciones');
            }
        }

        if (fechaFin) {
            fechaFin.removeAttribute('type');
            if (fechaFin._flatpickr) fechaFin._flatpickr.destroy();
            try { 
                flatpickr(fechaFin, base); 
                fechaFin.classList.add('input-fecha'); 
            } catch(error) {
                handleFlatpickrError(error, 'id_fecha_fin_vacaciones');
            }
        }

        const periodoVacacional = document.getElementById('id_periodo_vacacional');
        if (periodoVacacional) periodoVacacional.addEventListener('change', actualizarEstadoBoton);
        if (fechaInicio) { fechaInicio.addEventListener('input', actualizarEstadoBoton); fechaInicio.addEventListener('keyup', actualizarEstadoBoton); }
        if (fechaFin)    { fechaFin.addEventListener('input', actualizarEstadoBoton);    fechaFin.addEventListener('keyup', actualizarEstadoBoton); }

        actualizarEstadoBoton();
    }

    function esperarVariablesEInicializar() {
        function listas() {
            const festivosDisp = window.FESTIVOS_COLOMBIA && Array.isArray(window.FESTIVOS_COLOMBIA);
            const estamentoDisp = window.FUNCIONARIO_ESTAMENTO !== undefined;
            return festivosDisp && estamentoDisp;
        }

        function esperarVariablesConFallback() {
            if (listas()) {
                esperarFlatpickr(inicializarFlatpickr);
            } else {
                requestAnimationFrame(function() {
                    if (listas()) {
                        esperarFlatpickr(inicializarFlatpickr);
                    } else {
                        esperarFlatpickr(initFlatpickrSinValidacion);
                    }
                });
            }
        }

        document.addEventListener('variablesGlobalesListas', function() {
            if (listas()) esperarFlatpickr(inicializarFlatpickr);
        });

        if (listas()) {
            esperarFlatpickr(inicializarFlatpickr);
        } else {
            requestAnimationFrame(esperarVariablesConFallback);
        }
    }

    ready(function() {
        esperarVariablesEInicializar();
    });
})();
