/**
 * Calcula los días totales de vacaciones basado en las fechas seleccionadas
 * y el tipo de días (calendario o hábiles).
 */
document.addEventListener('DOMContentLoaded', function() {
  const fechaInicio = document.getElementById('id_fecha_inicio_vacaciones');
  const fechaFin = document.getElementById('id_fecha_fin_vacaciones');
  const tipoHabiles = document.getElementById('id_tipo_habiles');
  const tipoCalendario = document.getElementById('id_tipo_calendario');
  const totalDias = document.getElementById('id_total_dias_solicitados');

  if (fechaInicio && fechaFin && totalDias) {
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

    function calcularDias() {
      if (!fechaInicio.value || !fechaFin.value) {
        totalDias.value = '';
        return;
      }

      const inicio = parseFechaDMY(fechaInicio.value);
      const fin = parseFechaDMY(fechaFin.value);

      if (!inicio || !fin || inicio > fin) {
        totalDias.value = '';
        return;
      }

      const diffTime = Math.abs(fin - inicio);
      const diasCalculados = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
      totalDias.value = diasCalculados;
      totalDias.dispatchEvent(new Event('change', { bubbles: true }));
      totalDias.dispatchEvent(new Event('input', { bubbles: true }));
    }

    function calcularFechaFinAutomatico() {
      if (!fechaInicio.value) return;

      const inicio = parseFechaDMY(fechaInicio.value);

      if (!inicio) return;

      let fechaFinCalculada = null;
      const estamento = (window.FUNCIONARIO_ESTAMENTO || '').toLowerCase();
      const decreto = (window.FUNCIONARIO_DECRETO || '').trim();

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

      if (fechaFinCalculada) {
        const dia = String(fechaFinCalculada.getDate()).padStart(2, '0');
        const mes = String(fechaFinCalculada.getMonth() + 1).padStart(2, '0');
        const anio = fechaFinCalculada.getFullYear();
        fechaFin.value = `${dia}/${mes}/${anio}`;
        
        if (fechaFin._flatpickr) {
          fechaFin._flatpickr.setDate(fechaFin.value, true, 'd/m/Y');
        }
        calcularDias();
      }
    }

    if (window.flatpickr) {
      if (fechaInicio._flatpickr) {
        fechaInicio._flatpickr.config.onChange.push(calcularDias);
        fechaInicio._flatpickr.config.onChange.push(calcularFechaFinAutomatico);
      }
      if (fechaFin._flatpickr) {
        fechaFin._flatpickr.config.onChange.push(calcularDias);
      }
    }

    fechaInicio.addEventListener('change', calcularDias);
    fechaFin.addEventListener('change', calcularDias);

    if (tipoHabiles) tipoHabiles.addEventListener('change', calcularDias);
    if (tipoCalendario) tipoCalendario.addEventListener('change', calcularDias);
    if (fechaInicio.value && fechaFin.value) {
      calcularDias();
    }
  }
}); 
