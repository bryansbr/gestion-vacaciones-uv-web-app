function mostrarTab(tab) {
  document.querySelectorAll('.tab-content').forEach(content => {
    content.classList.remove('active');
  });
  document.querySelectorAll('.tab-button').forEach(button => {
    button.classList.remove('active');
  });
  
  document.getElementById('tab-content-' + tab).classList.add('active');
  document.getElementById('tab-' + tab).classList.add('active');
}

function convertirFechaDDMMYYYYaYYYYMMDD(fechaStr) {
  if (!fechaStr) return '';
  const partes = fechaStr.split('/');
  if (partes.length !== 3) return '';
  return partes[2] + '-' + partes[1] + '-' + partes[0];
}

function inicializarFlatpickrFiltros() {
  if (typeof flatpickr === 'undefined') {
    console.warn('Flatpickr no está disponible');
    return;
  }

  const fechaInicioInput = document.getElementById('fecha_inicio');
  const fechaFinInput = document.getElementById('fecha_fin');
  const fechaHoy = new Date();
  fechaHoy.setHours(23, 59, 59, 999);

  const configBase = {
    dateFormat: 'd/m/Y',
    allowInput: true,
    maxDate: fechaHoy,
    locale: {
      firstDayOfWeek: 1,
      weekdays: {
        shorthand: ['Do', 'Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sa'],
        longhand: ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'],
      },
      months: {
        shorthand: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'],
        longhand: ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'],
      },
    },
    onChange: function(selectedDates, dateStr, instance) {
      if (selectedDates.length > 0) {
        const fecha = selectedDates[0];
        const y = fecha.getFullYear();
        const m = String(fecha.getMonth() + 1).padStart(2, '0');
        const d = String(fecha.getDate()).padStart(2, '0');
        instance.input.setAttribute('data-django-format', `${y}-${m}-${d}`);
      }
    }
  };

  if (fechaInicioInput) {
    if (fechaInicioInput._flatpickr) {
      fechaInicioInput._flatpickr.destroy();
    }
    try {
      const configInicio = Object.assign({}, configBase);
      flatpickr(fechaInicioInput, configInicio);
      if (fechaInicioInput.value && /^\d{2}\/\d{2}\/\d{4}$/.test(fechaInicioInput.value)) {
        fechaInicioInput._flatpickr.setDate(fechaInicioInput.value, false, 'd/m/Y');
      }
    } catch (error) {
      console.error('Error al inicializar Flatpickr en fecha_inicio:', error);
    }
  }

  if (fechaFinInput) {
    if (fechaFinInput._flatpickr) {
      fechaFinInput._flatpickr.destroy();
    }
    try {
      const configFin = Object.assign({}, configBase);
      flatpickr(fechaFinInput, configFin);
      if (fechaFinInput.value && /^\d{2}\/\d{2}\/\d{4}$/.test(fechaFinInput.value)) {
        fechaFinInput._flatpickr.setDate(fechaFinInput.value, false, 'd/m/Y');
      }
    } catch (error) {
      console.error('Error al inicializar Flatpickr en fecha_fin:', error);
    }
  }

  const formFiltros = document.getElementById('form-filtros');
  if (formFiltros) {
    formFiltros.addEventListener('submit', function(e) {
      if (fechaInicioInput && fechaInicioInput.value) {
        if (fechaInicioInput._flatpickr && fechaInicioInput._flatpickr.selectedDates.length > 0) {
          const fechaSeleccionada = fechaInicioInput._flatpickr.selectedDates[0];
          const y = fechaSeleccionada.getFullYear();
          const m = String(fechaSeleccionada.getMonth() + 1).padStart(2, '0');
          const d = String(fechaSeleccionada.getDate()).padStart(2, '0');
          fechaInicioInput.value = `${y}-${m}-${d}`;
        } else if (/^\d{2}\/\d{2}\/\d{4}$/.test(fechaInicioInput.value)) {
          const fechaConvertida = convertirFechaDDMMYYYYaYYYYMMDD(fechaInicioInput.value);
          if (fechaConvertida) {
            fechaInicioInput.value = fechaConvertida;
          }
        } else if (fechaInicioInput.getAttribute('data-django-format')) {
          fechaInicioInput.value = fechaInicioInput.getAttribute('data-django-format');
        }
      }
      
      if (fechaFinInput && fechaFinInput.value) {
        if (fechaFinInput._flatpickr && fechaFinInput._flatpickr.selectedDates.length > 0) {
          const fechaSeleccionada = fechaFinInput._flatpickr.selectedDates[0];
          const y = fechaSeleccionada.getFullYear();
          const m = String(fechaSeleccionada.getMonth() + 1).padStart(2, '0');
          const d = String(fechaSeleccionada.getDate()).padStart(2, '0');
          fechaFinInput.value = `${y}-${m}-${d}`;
        } else if (/^\d{2}\/\d{2}\/\d{4}$/.test(fechaFinInput.value)) {
          const fechaConvertida = convertirFechaDDMMYYYYaYYYYMMDD(fechaFinInput.value);
          if (fechaConvertida) {
            fechaFinInput.value = fechaConvertida;
          }
        } else if (fechaFinInput.getAttribute('data-django-format')) {
          fechaFinInput.value = fechaFinInput.getAttribute('data-django-format');
        }
      }

    });
  }
}

document.addEventListener('DOMContentLoaded', function() {
  if (typeof flatpickr !== 'undefined') {
    inicializarFlatpickrFiltros();
  } else {
    const checkFlatpickr = setInterval(function() {
      if (typeof flatpickr !== 'undefined') {
        clearInterval(checkFlatpickr);
        inicializarFlatpickrFiltros();
      }
    }, 100);
    
    setTimeout(function() {
      clearInterval(checkFlatpickr);
      if (typeof flatpickr === 'undefined') {
        console.warn('Flatpickr no se cargó después de 5 segundos');
      }
    }, 5000);
  }
});

window.mostrarTab = mostrarTab;
