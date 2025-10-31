/**
 * Calcula los días totales de vacaciones basado en las fechas seleccionadas
 * y el tipo de días (calendario o hábiles).
 */
document.addEventListener('DOMContentLoaded', function() {
  function elementosListos() {
    const fechaInicio = document.getElementById('id_fecha_inicio_vacaciones');
    const fechaFin = document.getElementById('id_fecha_fin_vacaciones');
    return fechaInicio && fechaFin;
  }

  function inicializarCalculadora() {
    const fechaInicio = document.getElementById('id_fecha_inicio_vacaciones');
    const fechaFin = document.getElementById('id_fecha_fin_vacaciones');
    const periodoVacacional = document.getElementById('id_periodo_vacacional');
    const disfruteDiasPendientes = document.getElementById('id_tiene_dias_pendientes');

    const reintegrosPendientes = window.REINTEGROS_PENDIENTES || [];

    if (fechaInicio && fechaFin) {
      function parseFechaYMD(fechaStr) {
        if (!fechaStr) return null;

        if (fechaStr.includes('-')) {
          const partes = fechaStr.split('-');

          if (partes.length !== 3) return null;

          const year = parseInt(partes[0]);
          const month = parseInt(partes[1]);
          const day = parseInt(partes[2]);

          if (isNaN(year) || isNaN(month) || isNaN(day)) return null;
          return new Date(year, month - 1, day);

        } else if (fechaStr.includes('/')) {
          const partes = fechaStr.split('/');

          if (partes.length !== 3) return null;
          const day = parseInt(partes[0]);
          const month = parseInt(partes[1]);
          const year = parseInt(partes[2]);

          if (isNaN(year) || isNaN(month) || isNaN(day)) return null;
          return new Date(year, month - 1, day);
        }
        return null;
      }

      function formatFechaYMD(fecha) {
        const dia = String(fecha.getDate()).padStart(2, '0');
        const mes = String(fecha.getMonth() + 1).padStart(2, '0');
        const anio = fecha.getFullYear();

        return `${anio}-${mes}-${dia}`;
      }

      function addDays(date, days) {
        const result = new Date(date);
        result.setDate(result.getDate() + days);

        return result;
      }

      function addBusinessDays(date, days, festivos) {
        const toFestivoKey = (d) => {
          const dd = String(d.getDate()).padStart(2,'0');
          const mm = String(d.getMonth()+1).padStart(2,'0');
          const yy = d.getFullYear();
          return `${dd}/${mm}/${yy}`;
        };
      
        const isWeekend = (d) => d.getDay() === 0 || d.getDay() === 6;
        const isHoliday = (d) => (window.FESTIVOS_COLOMBIA || []).includes(toFestivoKey(d));
      
        let result = new Date(date);
        let added = 0;
      
        while (added < days) {
          if (!isWeekend(result) && !isHoliday(result)) {
            added++;
            if (added === days) break;
          }
          result.setDate(result.getDate() + 1);
        }
        return result;
      }      

      function obtenerDiasPendientesReintegro() {
        if (!periodoVacacional || !disfruteDiasPendientes) return null;
        
        const periodoId = periodoVacacional.value;
        const esDisfrutePendientes = disfruteDiasPendientes.checked;
        
        if (!esDisfrutePendientes || !periodoId) return null;

        const reintegro = reintegrosPendientes.find(r => r.periodo_vacacional_id === parseInt(periodoId));
        
        return reintegro ? {
          dias: reintegro.dias_pendientes,
          tipo: reintegro.tipo_dias
        } : null;
      }

      function calcularFechaFinAutomatico() {
        if (!fechaInicio.value) return;

        const inicio = parseFechaYMD(fechaInicio.value);

        if (!inicio) return;

        let fechaFinCalculada = null;
        const estamento = (window.FUNCIONARIO_ESTAMENTO || '').toLowerCase();
        const decreto = (window.FUNCIONARIO_DECRETO || '').trim();
        
        const diasPendientes = obtenerDiasPendientesReintegro();
        
        if (diasPendientes) {
          if (diasPendientes.tipo === 'H') {
            fechaFinCalculada = addBusinessDays(inicio, diasPendientes.dias, window.FESTIVOS_COLOMBIA);
          } else {
            fechaFinCalculada = addDays(inicio, diasPendientes.dias);
          }
        } else {
          let diasPendientesPeriodo = null;
          if (periodoVacacional && periodoVacacional.value) {
            const periodosDiasPendientes = window.PERIODOS_DIAS_PENDIENTES || {};
            const periodoId = parseInt(periodoVacacional.value);
            diasPendientesPeriodo = periodosDiasPendientes[periodoId] || null;
          }

          let diasACalcular = null;
          if (estamento === 'docente' && decreto === '1279') {
            diasACalcular = 30;
          } else if (estamento === 'docente' && decreto === '115') {
            diasACalcular = 30;
          } else if (estamento === 'administrativo') {
            diasACalcular = 15;
          } else if (estamento === 'trabajador oficial') {
            diasACalcular = 30;
          } else {
            diasACalcular = 15;
          }

          if (diasPendientesPeriodo !== null && diasPendientesPeriodo !== undefined) {
            diasACalcular = Math.min(diasACalcular, diasPendientesPeriodo);
          }

          if (estamento === 'docente' && decreto === '1279') {
            const diasHabiles = Math.min(15, diasACalcular);
            const diasCalendario = Math.max(0, diasACalcular - 15);
            const ultimoHabil = addBusinessDays(inicio, diasHabiles, window.FESTIVOS_COLOMBIA);
            const result = new Date(ultimoHabil);
            result.setDate(result.getDate() + diasCalendario);
            fechaFinCalculada = result;
          } else if (estamento === 'administrativo') {
            fechaFinCalculada = addBusinessDays(inicio, diasACalcular, window.FESTIVOS_COLOMBIA);
          } else {
            fechaFinCalculada = addDays(inicio, diasACalcular - 1);
          }
        }

        if (fechaFinCalculada) {
          const fechaFormateada = formatFechaYMD(fechaFinCalculada);
          fechaFin.value = fechaFormateada;

          if (fechaFin._flatpickr) {
            fechaFin._flatpickr.setDate(fechaFormateada, true, 'Y-m-d');
          }
          
          const event = new Event('change', { bubbles: true });
          fechaFin.dispatchEvent(event);
        }
      }

      function configurarEventListeners() {
        fechaInicio.addEventListener('change', function() {
          requestAnimationFrame(calcularFechaFinAutomatico);
        });

        if (fechaInicio._flatpickr) {
          fechaInicio._flatpickr.config.onChange.push(function(selectedDates, dateStr, instance) {
            requestAnimationFrame(calcularFechaFinAutomatico);
          });
        }

        if (periodoVacacional) {
          periodoVacacional.addEventListener('change', function() {
            requestAnimationFrame(calcularFechaFinAutomatico);
          });
        }

        if (disfruteDiasPendientes) {
          disfruteDiasPendientes.addEventListener('change', function() {
            requestAnimationFrame(calcularFechaFinAutomatico);
          });
        }
      }

      function esperarFlatpickr() {
        if (fechaInicio._flatpickr && fechaFin._flatpickr) {
          configurarEventListeners();
        } else {
          requestAnimationFrame(esperarFlatpickr);
        }
      }

      esperarFlatpickr();
    }
  }

  function esperarElementos() {
    if (elementosListos()) {
      inicializarCalculadora();
    } else {
      requestAnimationFrame(esperarElementos);
    }
  }
  esperarElementos();
}); 
