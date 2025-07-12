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

  // Obtener reintegros pendientes del contexto
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
      
      // Buscar reintegro pendiente para el periodo seleccionado
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
      
      // Verificar si hay días pendientes de reintegro
      const diasPendientes = obtenerDiasPendientesReintegro();
      
      if (diasPendientes) {
        // Calcular fecha fin basada en días pendientes
        if (diasPendientes.tipo === 'H') {
          fechaFinCalculada = addBusinessDays(inicio, diasPendientes.dias, window.FESTIVOS_COLOMBIA);
        } else {
          fechaFinCalculada = addDays(inicio, diasPendientes.dias);
        }
      } else {
        // Cálculo normal según estamento y decreto
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

    // Función para actualizar la fecha mínima cuando cambie el checkbox de días pendientes
    function actualizarFechaMinima() {
      const hoy = new Date();
      hoy.setHours(0, 0, 0, 0);
      
      const esDisfrutePendientes = disfruteDiasPendientes && disfruteDiasPendientes.checked;
      
      if (esDisfrutePendientes) {
        // Para días pendientes: permite solicitar con un día de anticipación
        const fechaMinima = new Date(hoy);
        fechaMinima.setDate(hoy.getDate() + 1);
        
        // Función auxiliar para obtener siguiente día hábil
        function obtenerSiguienteDiaHabil(fecha) {
          let siguienteDia = new Date(fecha);
          while (siguienteDia.getDay() === 0 ||
                 siguienteDia.getDay() === 6 ||
                 (window.FESTIVOS_COLOMBIA || []).includes(
                   `${String(siguienteDia.getDate()).padStart(2, '0')}/${String(siguienteDia.getMonth() + 1).padStart(2, '0')}/${siguienteDia.getFullYear()}`
                 )) {
            siguienteDia.setDate(siguienteDia.getDate() + 1);
          }
          return siguienteDia;
        }
        
        const fechaMinimaHabil = obtenerSiguienteDiaHabil(fechaMinima);
        
        if (fechaInicio._flatpickr) {
          fechaInicio._flatpickr.config.minDate = fechaMinimaHabil;
          fechaInicio._flatpickr.redraw();
        }
      } else {
        // Para vacaciones nuevas: recalcular según calendario de pagos
        const estamento = (window.FUNCIONARIO_ESTAMENTO || '').toLowerCase();
        const decreto = (window.FUNCIONARIO_DECRETO || '').trim();
        
        let fechaSalida = new Date();
        
        if (estamento === 'docente') {
          // Docentes: pago el día 30 de cada mes
          // Plazo máximo: día 10 del mes para salir el 1º del mes siguiente
          if (hoy.getDate() <= 10) {
            // Si estamos antes del día 10, puede salir el 1º del mes siguiente
            if (hoy.getMonth() === 11) { // Diciembre
              fechaSalida = new Date(hoy.getFullYear() + 1, 0, 1); // 1 de enero del año siguiente
            } else {
              fechaSalida = new Date(hoy.getFullYear(), hoy.getMonth() + 1, 1);
            }
          } else {
            // Si estamos después del día 10, debe esperar hasta el 1º del mes siguiente al próximo
            if (hoy.getMonth() === 11) { // Diciembre
              fechaSalida = new Date(hoy.getFullYear() + 1, 1, 1); // 1 de febrero del año siguiente
            } else if (hoy.getMonth() === 10) { // Noviembre
              fechaSalida = new Date(hoy.getFullYear() + 1, 0, 1); // 1 de enero del año siguiente
            } else {
              fechaSalida = new Date(hoy.getFullYear(), hoy.getMonth() + 2, 1);
            }
          }
        } else {
          // Administrativos y trabajadores oficiales: pago quincenal (15 y 30)
          // Plazo máximo: día 3 para salir el 16, día 17 para salir el 1º del mes siguiente
          if (hoy.getDate() <= 3) {
            // Puede salir el 16 del mes actual
            fechaSalida = new Date(hoy.getFullYear(), hoy.getMonth(), 16);
          } else if (hoy.getDate() <= 17) {
            // Puede salir el 1º del mes siguiente
            if (hoy.getMonth() === 11) { // Diciembre
              fechaSalida = new Date(hoy.getFullYear() + 1, 0, 1); // 1 de enero del año siguiente
            } else {
              fechaSalida = new Date(hoy.getFullYear(), hoy.getMonth() + 1, 1);
            }
          } else {
            // Debe esperar hasta el 16 del mes siguiente
            if (hoy.getMonth() === 11) { // Diciembre
              fechaSalida = new Date(hoy.getFullYear() + 1, 0, 16); // 16 de enero del año siguiente
            } else {
              fechaSalida = new Date(hoy.getFullYear(), hoy.getMonth() + 1, 16);
            }
          }
        }
        
        // Función auxiliar para obtener siguiente día hábil
        function obtenerSiguienteDiaHabil(fecha) {
          let siguienteDia = new Date(fecha);
          while (siguienteDia.getDay() === 0 ||
                 siguienteDia.getDay() === 6 ||
                 (window.FESTIVOS_COLOMBIA || []).includes(
                   `${String(siguienteDia.getDate()).padStart(2, '0')}/${String(siguienteDia.getMonth() + 1).padStart(2, '0')}/${siguienteDia.getFullYear()}`
                 )) {
            siguienteDia.setDate(siguienteDia.getDate() + 1);
          }
          return siguienteDia;
        }
        
        const fechaMinimaHabil = obtenerSiguienteDiaHabil(fechaSalida);
        
        if (fechaInicio._flatpickr) {
          fechaInicio._flatpickr.config.minDate = fechaMinimaHabil;
          fechaInicio._flatpickr.redraw();
        }
      }
    }

    // Event listeners
    if (window.flatpickr) {
      if (fechaInicio._flatpickr) {
        fechaInicio._flatpickr.config.onChange.push(calcularFechaFinAutomatico);
      }
    }

    if (periodoVacacional) {
      periodoVacacional.addEventListener('change', calcularFechaFinAutomatico);
    }

    if (disfruteDiasPendientes) {
      disfruteDiasPendientes.addEventListener('change', function() {
        actualizarFechaMinima();
        calcularFechaFinAutomatico();
      });
    }

    // Calcular fecha fin inicial si hay valores
    if (fechaInicio.value && fechaFin.value) {
      calcularFechaFinAutomatico();
    }
  }
}); 
