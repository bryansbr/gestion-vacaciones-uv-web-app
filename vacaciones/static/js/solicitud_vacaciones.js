/**
 * Calcula los días totales de vacaciones basado en las fechas seleccionadas
 * y el tipo de días (calendario o hábiles).
 */
document.addEventListener('DOMContentLoaded', function() {
  const fechaInicio = document.getElementById('id_fecha_inicio_vacaciones');
  const fechaFin = document.getElementById('id_fecha_fin_vacaciones');
  const tipoDias = document.getElementById('id_tipo_dias_solicitados');
  const totalDias = document.getElementById('id_total_dias_solicitados');

  // Convierte una fecha en formato dd/mm/yyyy a un objeto Date
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

    let diasCalculados;

    if (tipoDias.value === 'C') {
      const diffTime = Math.abs(fin - inicio);
      diasCalculados = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
    } else {
      // Días hábiles: contar solo días de lunes a viernes
      let diasHabiles = 0;
      const current = new Date(inicio);

      while (current <= fin) {
        if (current.getDay() !== 0 && current.getDay() !== 6) {
          diasHabiles++;
        }
        current.setDate(current.getDate() + 1);
      }
      diasCalculados = diasHabiles;
    }
    
    totalDias.value = diasCalculados;
    totalDias.dispatchEvent(new Event('change', { bubbles: true }));
    totalDias.dispatchEvent(new Event('input', { bubbles: true }));
  }

  fechaInicio.addEventListener('change', calcularDias);
  fechaFin.addEventListener('change', calcularDias);
  tipoDias.addEventListener('change', calcularDias);

  if (fechaInicio.value && fechaFin.value) {
    calcularDias();
  }
}); 
