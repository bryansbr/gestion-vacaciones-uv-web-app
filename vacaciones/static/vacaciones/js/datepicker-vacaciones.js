document.addEventListener('DOMContentLoaded', function() {
  const festivosColombia = window.FESTIVOS_COLOMBIA || [];

  function esFestivo(fecha) {
    const dia = String(fecha.getDate()).padStart(2, '0');
    const mes = String(fecha.getMonth() + 1).padStart(2, '0');
    const anio = fecha.getFullYear();
    const fechaFormatoFestivo = `${dia}/${mes}/${anio}`;
    return festivosColombia.includes(fechaFormatoFestivo);
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
    
    const disfruteDiasPendientes = document.getElementById('id_tiene_dias_pendientes');
    const esDisfrutePendientes = disfruteDiasPendientes && disfruteDiasPendientes.checked;
    
    if (esDisfrutePendientes) {
      const fechaMinima = new Date(hoy);
      fechaMinima.setDate(hoy.getDate() + 1);
      return obtenerSiguienteDiaHabil(fechaMinima);
    } else {
      const estamento = (window.FUNCIONARIO_ESTAMENTO || '').toLowerCase();
      let fechaSalida = new Date();
      
      if (estamento === 'docente') {
        if (hoy.getDate() <= 10) {
          if (hoy.getMonth() === 11) {
            fechaSalida = new Date(hoy.getFullYear() + 1, 0, 1);
          } else {
            fechaSalida = new Date(hoy.getFullYear(), hoy.getMonth() + 1, 1);
          }
        } else {
          if (hoy.getMonth() === 11) {
            fechaSalida = new Date(hoy.getFullYear() + 1, 1, 1);
          } else if (hoy.getMonth() === 10) {
            fechaSalida = new Date(hoy.getFullYear() + 1, 0, 1);
          } else {
            fechaSalida = new Date(hoy.getFullYear(), hoy.getMonth() + 2, 1);
          }
        }
      } else {
        if (hoy.getDate() <= 3) {
          fechaSalida = new Date(hoy.getFullYear(), hoy.getMonth(), 16);
        } else if (hoy.getDate() <= 17) {
          if (hoy.getMonth() === 11) {
            fechaSalida = new Date(hoy.getFullYear() + 1, 0, 1);
          } else {
            fechaSalida = new Date(hoy.getFullYear(), hoy.getMonth() + 1, 1);
          }
        } else {
          if (hoy.getMonth() === 11) {
            fechaSalida = new Date(hoy.getFullYear() + 1, 0, 16);
          } else {
            fechaSalida = new Date(hoy.getFullYear(), hoy.getMonth() + 1, 16);
          }
        }
      }

      return obtenerSiguienteDiaHabil(fechaSalida);
    }
  }

  const fechaMinimaInicio = calcularFechaMinimaInicio();
  const localeConfig = {
    firstDayOfWeek: 1,
    weekdays: {
      shorthand: ["Do", "Lu", "Ma", "Mi", "Ju", "Vi", "Sa"],
      longhand: ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"],
    },
    months: {
      shorthand: ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
      longhand: ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"],
    },
  };

  try {
    flatpickr("#id_fecha_inicio_vacaciones", {
      dateFormat: "Y-m-d",
      allowInput: true,
      minDate: fechaMinimaInicio,
      locale: localeConfig,
      disable: [
        function(date) {
          return date.getDay() === 0 || date.getDay() === 6 || esFestivo(date);
        }
      ]
    });

    flatpickr("#id_fecha_fin_vacaciones", {
      dateFormat: "Y-m-d",
      allowInput: true,
      locale: localeConfig
    });

    document.getElementById('id_fecha_inicio_vacaciones').classList.add('input-fecha');
    document.getElementById('id_fecha_fin_vacaciones').classList.add('input-fecha');
  } catch (error) {

    const inputs = document.querySelectorAll('#id_fecha_inicio_vacaciones, #id_fecha_fin_vacaciones');
    inputs.forEach(input => {
      input.type = 'date';
      input.classList.add('input-fecha');
    });
  }
});
