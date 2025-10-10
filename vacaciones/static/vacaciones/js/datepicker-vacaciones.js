(function() {
    'use strict';

    // ----------------- Helpers DOM / Ready -----------------
    function ready(fn) {
        if (document.readyState !== 'loading') fn();
        else document.addEventListener('DOMContentLoaded', fn);
    }

    function waitForFlatpickr(callback, maxAttempts = 50) {
        let attempts = 0;
        (function check() {
            attempts++;
            if (typeof flatpickr !== 'undefined') callback();
            else if (attempts < maxAttempts) setTimeout(check, 100);
        })();
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
        while (cont < n) {
            f.setDate(f.getDate() + 1);
            if (!esFinDeSemana(f) && !esFestivo(f)) cont++;
        }
        return f;
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
                return sumarDiasCalendario(finHabiles, 15);
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
    function initFlatpickr() {
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
                        // Autocalcular fecha fin SOLO cuando el usuario cambia inicio
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
            try { flatpickr(fechaInicio, configInicio); fechaInicio.classList.add('input-fecha'); } catch(_) {}
        }

        if (fechaFin) {
            fechaFin.removeAttribute('type');
            if (fechaFin._flatpickr) fechaFin._flatpickr.destroy();
            try { flatpickr(fechaFin, configFin); fechaFin.classList.add('input-fecha'); } catch(_) {}
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

        // Convertir a YYYY-mm-dd en submit (si vienen en dd/mm/YYYY)
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

        // Listeners para revalidar y habilitar botón
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
            try { flatpickr(fechaInicio, base); } catch(_) {}
        }

        if (fechaFin) {
            fechaFin.removeAttribute('type');
            if (fechaFin._flatpickr) fechaFin._flatpickr.destroy();
            try { flatpickr(fechaFin, base); } catch(_) {}
        }

        const periodoVacacional = document.getElementById('id_periodo_vacacional');
        if (periodoVacacional) periodoVacacional.addEventListener('change', actualizarEstadoBoton);
        if (fechaInicio) { fechaInicio.addEventListener('input', actualizarEstadoBoton); fechaInicio.addEventListener('keyup', actualizarEstadoBoton); }
        if (fechaFin)    { fechaFin.addEventListener('input', actualizarEstadoBoton);    fechaFin.addEventListener('keyup', actualizarEstadoBoton); }

        actualizarEstadoBoton();
    }

    function esperarVariablesYInicializar() {
        function listas() {
            const festivosDisp = window.FESTIVOS_COLOMBIA && Array.isArray(window.FESTIVOS_COLOMBIA);
            const estamentoDisp = window.FUNCIONARIO_ESTAMENTO !== undefined;
            return festivosDisp && estamentoDisp;
        }

        document.addEventListener('variablesGlobalesListas', function() {
            if (listas()) waitForFlatpickr(initFlatpickr);
        });

        setTimeout(function() {
            if (listas()) {
                waitForFlatpickr(initFlatpickr);
            } else {
                setTimeout(function() {
                    if (listas()) waitForFlatpickr(initFlatpickr);
                    else {
                        waitForFlatpickr(initFlatpickrSinValidacion);
                    }
                }, 1000);
            }
        }, 500);
    }

    ready(function() {
        esperarVariablesYInicializar();
    });

})();
