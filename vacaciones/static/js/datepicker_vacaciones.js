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
    const fechaMinima = new Date(hoy);
    fechaMinima.setDate(hoy.getDate() + 16);
    const siguienteHabil = obtenerSiguienteDiaHabil(fechaMinima);
    siguienteHabil.setHours(0, 0, 0, 0);
    return siguienteHabil;
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
});
