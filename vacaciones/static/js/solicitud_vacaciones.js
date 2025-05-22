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

    if (window.flatpickr) {
      if (fechaInicio._flatpickr) {
        fechaInicio._flatpickr.config.onChange.push(calcularDias);
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
