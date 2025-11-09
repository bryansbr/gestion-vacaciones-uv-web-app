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
      function parsearFecha(fechaStr) {
        if (!fechaStr) return null;

        if (fechaStr.includes('-')) {
          const partes = fechaStr.split('-');

          if (partes.length !== 3) return null;

          const anio = parseInt(partes[0]);
          const mes = parseInt(partes[1]);
          const dia = parseInt(partes[2]);

          if (isNaN(anio) || isNaN(mes) || isNaN(dia)) return null;
          return new Date(anio, mes - 1, dia);

        } else if (fechaStr.includes('/')) {
          const partes = fechaStr.split('/');

          if (partes.length !== 3) return null;
          const dia = parseInt(partes[0]);
          const mes = parseInt(partes[1]);
          const anio = parseInt(partes[2]);

          if (isNaN(anio) || isNaN(mes) || isNaN(dia)) return null;
          return new Date(anio, mes - 1, dia);
        }
        return null;
      }

      function formatearFecha(fecha) {
        const dia = String(fecha.getDate()).padStart(2, '0');
        const mes = String(fecha.getMonth() + 1).padStart(2, '0');
        const anio = fecha.getFullYear();

        return `${anio}-${mes}-${dia}`;
      }

      function agregarDias(date, days) {
        const resultado = new Date(date);
        resultado.setDate(resultado.getDate() + days);

        return resultado;
      }

      function agregarDiasLaborales(date, days, festivos) {
        const aFestivoKey = (d) => {
          const dd = String(d.getDate()).padStart(2,'0');
          const mm = String(d.getMonth()+1).padStart(2,'0');
          const yy = d.getFullYear();
          return `${dd}/${mm}/${yy}`;
        };
      
        const esFinDeSemana = (d) => d.getDay() === 0 || d.getDay() === 6;
        const esFestivo = (d) => (window.FESTIVOS_COLOMBIA || []).includes(aFestivoKey(d));
      
        let resultado = new Date(date);
        let agregado = 0;
      
        while (agregado < days) {
          if (!esFinDeSemana(resultado) && !esFestivo(resultado)) {
            agregado++;
            if (agregado === days) break;
          }
          resultado.setDate(resultado.getDate() + 1);
        }
        return resultado;
      }      

      function obtenerDiasPendientesReintegro() {
        if (!periodoVacacional || !disfruteDiasPendientes) return null;
        
        const idPeriodo = periodoVacacional.value;
        const esDisfrutePendientes = disfruteDiasPendientes.checked;
        
        if (!esDisfrutePendientes || !idPeriodo) return null;

        const reintegro = reintegrosPendientes.find(r => r.periodo_vacacional_id === parseInt(idPeriodo));
        
        return reintegro ? {
          dias: reintegro.dias_pendientes,
          tipo: reintegro.tipo_dias
        } : null;
      }

      function calcularFechaFinAutomatico() {
        if (!fechaInicio.value) return;

        const inicio = parsearFecha(fechaInicio.value);

        if (!inicio) return;

        let fechaFinCalculada = null;
        const estamento = (window.FUNCIONARIO_ESTAMENTO || '').toLowerCase();
        const decreto = (window.FUNCIONARIO_DECRETO || '').trim();
        
        const diasPendientes = obtenerDiasPendientesReintegro();
        
        if (diasPendientes) {
          if (diasPendientes.tipo === 'H') {
            fechaFinCalculada = agregarDiasLaborales(inicio, diasPendientes.dias, window.FESTIVOS_COLOMBIA);
          } else {
            fechaFinCalculada = agregarDias(inicio, diasPendientes.dias);
          }
        } else {
          let diasPendientesPeriodo = null;
          if (periodoVacacional && periodoVacacional.value) {
            const periodosDiasPendientes = window.PERIODOS_DIAS_PENDIENTES || {};
            const idPeriodo = parseInt(periodoVacacional.value);
            diasPendientesPeriodo = periodosDiasPendientes[idPeriodo] || null;
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
            const ultimoHabil = agregarDiasLaborales(inicio, diasHabiles, window.FESTIVOS_COLOMBIA);
            const resultado = new Date(ultimoHabil);
            resultado.setDate(resultado.getDate() + diasCalendario);
            fechaFinCalculada = resultado;
          } else if (estamento === 'administrativo') {
            fechaFinCalculada = agregarDiasLaborales(inicio, diasACalcular, window.FESTIVOS_COLOMBIA);
          } else {
            const offsetCalendario = Math.max(0, diasACalcular - 1);
            fechaFinCalculada = agregarDias(inicio, offsetCalendario);
          }
        }

        if (fechaFinCalculada) {
          const fechaFormateada = formatearFecha(fechaFinCalculada);
          fechaFin.value = fechaFormateada;

          if (fechaFin._flatpickr) {
            fechaFin._flatpickr.setDate(fechaFormateada, true, 'Y-m-d');
          }
          
          const evento = new Event('change', { bubbles: true });
          fechaFin.dispatchEvent(evento);
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
