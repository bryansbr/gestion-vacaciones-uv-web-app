/**
 * Calcula los días totales de vacaciones basado en las fechas seleccionadas
 * y el tipo de días (calendario o hábiles).
 */
document.addEventListener('DOMContentLoaded', function() {
  const fechaInicio = document.getElementById('id_fecha_inicio_vacaciones');
  const fechaFin = document.getElementById('id_fecha_fin_vacaciones');
  const tipoHabiles = document.getElementById('id_tipo_habiles');
  const tipoCalendario = document.getElementById('id_tipo_calendario');
  const periodoVacacional = document.getElementById('id_periodo_vacacional');
  const disfruteDiasPendientes = document.getElementById('id_disfrute_dias_pendientes');
  const reintegrosPendientes = window.REINTEGROS_PENDIENTES || [];

  if (fechaInicio && fechaFin) {
    function parseFechaDMY(fechaStr) {
      if (!fechaStr) return null;
      const partes = fechaStr.split('/');
      if (partes.length !== 3) return null;
      return new Date(parseInt(partes[2]), parseInt(partes[1]) - 1, parseInt(partes[0]));
    }

    function addDays(date, days) {
      const result = new Date(date);
      result.setDate(result.getDate() + (days - 1));
      return result;
    }

    function addBusinessDays(date, days, festivos) {
      let result = new Date(date);
      let added = 0;

      while (added < days) {
        const isWeekend = result.getDay() === 0 || result.getDay() === 6;
        const dia = String(result.getDate()).padStart(2, '0');
        const mes = String(result.getMonth() + 1).padStart(2, '0');
        const anio = result.getFullYear();
        const esFestivo = (window.FESTIVOS_COLOMBIA || []).includes(`${dia}/${mes}/${anio}`);
        
        if (!isWeekend && !esFestivo) {
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

      const inicio = parseFechaDMY(fechaInicio.value);
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
        if (estamento === 'docente' && decreto === '1279') {
          const ultimoHabil = addBusinessDays(inicio, 15, window.FESTIVOS_COLOMBIA);
          const primerCalendario = new Date(ultimoHabil);
          primerCalendario.setDate(primerCalendario.getDate() + 1);
          fechaFinCalculada = addDays(primerCalendario, 15);
        } else if (estamento === 'docente' && decreto === '115') {
          fechaFinCalculada = addDays(inicio, 30);
        } else if (estamento === 'administrativo') {
          fechaFinCalculada = addBusinessDays(inicio, 15, window.FESTIVOS_COLOMBIA);
        } else if (estamento === 'trabajador oficial') {
          fechaFinCalculada = addDays(inicio, 30);
        }
      }

      if (fechaFinCalculada) {
        const dia = String(fechaFinCalculada.getDate()).padStart(2, '0');
        const mes = String(fechaFinCalculada.getMonth() + 1).padStart(2, '0');
        const anio = fechaFinCalculada.getFullYear();
        fechaFin.value = `${dia}/${mes}/${anio}`;
        
        if (fechaFin._flatpickr) {
          fechaFin._flatpickr.setDate(fechaFin.value, true, 'd/m/Y');
        }
      }
    }

    if (window.flatpickr) {
      if (fechaInicio._flatpickr) {
        fechaInicio._flatpickr.config.onChange.push(calcularFechaFinAutomatico);
      }
    }

    if (periodoVacacional) {
      periodoVacacional.addEventListener('change', calcularFechaFinAutomatico);
    }

    if (disfruteDiasPendientes) {
      disfruteDiasPendientes.addEventListener('change', calcularFechaFinAutomatico);
    }

    if (fechaInicio.value && fechaFin.value) {
      calcularFechaFinAutomatico();
    }
  }
}); 
