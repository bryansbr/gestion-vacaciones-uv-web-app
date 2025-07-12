document.addEventListener('DOMContentLoaded', function() {
  const festivosColombia = window.FESTIVOS_COLOMBIA || [];

  function esFestivo(fecha) {
    const dia = String(fecha.getDate()).padStart(2, '0');
    const mes = String(fecha.getMonth() + 1).padStart(2, '0');
    const anio = fecha.getFullYear();
    
    return festivosColombia.includes(`${dia}/${mes}/${anio}`);
  }

  function obtenerSiguienteDiaHabil(fecha) {
    let siguienteDia = new Date(fecha);
    
    while (siguienteDia.getDay() === 0 ||
           siguienteDia.getDay() === 6 ||
           esFestivo(siguienteDia)) {
      siguienteDia.setDate(siguienteDia.getDate() + 1);
    }
    
    return siguienteDia;
  }

  function calcularFechaMinimaInicio() {
    const hoy = new Date();
    hoy.setHours(0, 0, 0, 0);
    
    // Verificar si es disfrute de días pendientes
    const disfruteDiasPendientes = document.getElementById('id_disfrute_dias_pendientes');
    const esDisfrutePendientes = disfruteDiasPendientes && disfruteDiasPendientes.checked;
    
    if (esDisfrutePendientes) {
      // Para días pendientes: permite solicitar con un día de anticipación
      const fechaMinima = new Date(hoy);
      fechaMinima.setDate(hoy.getDate() + 1);
      return obtenerSiguienteDiaHabil(fechaMinima);
    } else {
      // Para vacaciones nuevas: calcular según calendario de pagos
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
      
      // Asegurar que la fecha de salida sea un día hábil
      return obtenerSiguienteDiaHabil(fechaSalida);
    }
  }

  // Función para actualizar la fecha mínima cuando cambie el checkbox de días pendientes
  function actualizarFechaMinima() {
    const fechaMinimaInicio = calcularFechaMinimaInicio();
    const fechaInicioInput = document.getElementById('id_fecha_inicio_vacaciones');
    
    if (fechaInicioInput && fechaInicioInput._flatpickr) {
      fechaInicioInput._flatpickr.config.minDate = fechaMinimaInicio;
      fechaInicioInput._flatpickr.redraw();
    }
  }

  const fechaMinimaInicio = calcularFechaMinimaInicio();

  flatpickr("#id_fecha_inicio_vacaciones", {
    dateFormat: "d/m/Y",
    allowInput: true,
    minDate: fechaMinimaInicio,
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
    disable: [
      function(date) {
        return date.getDay() === 0 || date.getDay() === 6 || esFestivo(date);
      }
    ],
    onChange: function(selectedDates, _dateStr, instance) {
      if (selectedDates.length > 0) {
        const date = selectedDates[0];
  
        if (date.getDay() === 0 || date.getDay() === 6 || esFestivo(date)) {
          alert('La fecha seleccionada no es un día hábil. Por favor, elija un día hábil.');
          instance.clear();
        }
      }
    }
  });

  flatpickr("#id_fecha_fin_vacaciones", {
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
  });

  document.getElementById('id_fecha_inicio_vacaciones').classList.add('input-fecha');
  document.getElementById('id_fecha_fin_vacaciones').classList.add('input-fecha');

  // Agregar event listener para el checkbox de días pendientes
  const disfruteDiasPendientes = document.getElementById('id_disfrute_dias_pendientes');
  if (disfruteDiasPendientes) {
    disfruteDiasPendientes.addEventListener('change', actualizarFechaMinima);
  }
});
