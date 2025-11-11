(function () {
  const convertirValorEnFecha = (valor) => {
    if (!valor) {
      return null;
    }

    if (valor instanceof Date) {
      return valor;
    }

    if (typeof valor !== 'string') {
      return null;
    }

    const coincidenciaIso = valor.match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (coincidenciaIso) {
      const [, anio, mes, dia] = coincidenciaIso;
      return new Date(Number(anio), Number(mes) - 1, Number(dia));
    }

    const coincidenciaDmy = valor.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
    if (coincidenciaDmy) {
      const [, dia, mes, anio] = coincidenciaDmy;
      return new Date(Number(anio), Number(mes) - 1, Number(dia));
    }

    return null;
  };

  const formatearFechaIso = (fecha) => {
    if (!(fecha instanceof Date)) {
      return '';
    }
    const anio = fecha.getFullYear();
    const mes = String(fecha.getMonth() + 1).padStart(2, '0');
    const dia = String(fecha.getDate()).padStart(2, '0');
    return `${anio}-${mes}-${dia}`;
  };

  const formatearFechaParaMostrar = (fecha) => {
    if (!(fecha instanceof Date)) {
      return '';
    }
    const dia = String(fecha.getDate()).padStart(2, '0');
    const mes = String(fecha.getMonth() + 1).padStart(2, '0');
    const anio = fecha.getFullYear();
    return `${dia}/${mes}/${anio}`;
  };

  const actualizarResumenCampo = (campo, fechaInicio, fechaFin) => {
    if (!(fechaInicio instanceof Date)) {
      campo.value = '';
      return;
    }

    const fechaFinal = fechaFin instanceof Date ? fechaFin : fechaInicio;
    const textoInicio = formatearFechaParaMostrar(fechaInicio);
    const textoFin = formatearFechaParaMostrar(fechaFinal);
    campo.value = `Del ${textoInicio} al ${textoFin}`;
  };

  const configurarFlatpickr = (selector, opciones = {}) => {
    const campos = document.querySelectorAll(selector);
    if (typeof flatpickr === 'undefined' || !campos.length) {
      return;
    }

    campos.forEach((campo) => {
      if (campo.dataset.fpInitialized === '1') {
        return;
      }

      flatpickr(campo, Object.assign({
        dateFormat: 'd/m/Y',
        allowInput: true
      }, opciones));

      campo.dataset.fpInitialized = '1';
    });
  };

  const configurarFlatpickrRango = (selector, opciones = {}) => {
    const camposResumen = document.querySelectorAll(selector);
    if (typeof flatpickr === 'undefined' || !camposResumen.length) {
      return;
    }

    camposResumen.forEach((campoResumen) => {
      if (campoResumen.dataset.fpRangeInitialized === '1') {
        return;
      }

      const campoInicio = document.getElementById(campoResumen.dataset.rangeStartTarget);
      const campoFin = document.getElementById(campoResumen.dataset.rangeEndTarget);

      if (!campoInicio || !campoFin) {
        return;
      }

      const fechaInicio = convertirValorEnFecha(campoInicio.value);
      const fechaFin = convertirValorEnFecha(campoFin.value);
      const fechasPorDefecto = [];

      if (fechaInicio) {
        fechasPorDefecto.push(fechaInicio);
      }

      if (fechaFin) {
        fechasPorDefecto.push(fechaFin);
      }

      if (fechaInicio) {
        actualizarResumenCampo(campoResumen, fechaInicio, fechaFin);
      }

      if (campoResumen.disabled) {
        campoResumen.dataset.fpRangeInitialized = '1';
        return;
      }

      const sincronizarRango = (fechasSeleccionadas) => {
        if (!fechasSeleccionadas.length) {
          campoInicio.value = '';
          campoFin.value = '';
          campoResumen.value = '';
          return;
        }

        const [fechaSeleccionadaInicio, fechaSeleccionadaFin] = fechasSeleccionadas;
        const nuevaFechaInicio = fechaSeleccionadaInicio || convertirValorEnFecha(campoInicio.value);
        let nuevaFechaFin = fechaSeleccionadaFin || convertirValorEnFecha(campoFin.value);

        if (fechasSeleccionadas.length === 1 && fechaSeleccionadaInicio) {
          nuevaFechaFin = fechaSeleccionadaInicio;
        }

        if (nuevaFechaInicio instanceof Date) {
          campoInicio.value = formatearFechaIso(nuevaFechaInicio);
        }

        if (nuevaFechaFin instanceof Date) {
          campoFin.value = formatearFechaIso(nuevaFechaFin);
        } else if (!fechaSeleccionadaFin) {
          campoFin.value = '';
        }

        actualizarResumenCampo(campoResumen, nuevaFechaInicio, nuevaFechaFin);
      };

      const configuracion = Object.assign({
        mode: 'range',
        dateFormat: 'd/m/Y',
        allowInput: false,
        defaultDate: fechasPorDefecto,
        onReady: (fechasSeleccionadas) => {
          if (fechasSeleccionadas.length) {
            sincronizarRango(fechasSeleccionadas);
          } else {
            actualizarResumenCampo(campoResumen, fechaInicio, fechaFin);
          }
        },
        onChange: (fechasSeleccionadas) => {
          sincronizarRango(fechasSeleccionadas);
        },
        onClose: (fechasSeleccionadas) => {
          if (!fechasSeleccionadas.length) {
            sincronizarRango(fechasSeleccionadas);
          }
        }
      }, opciones);

      const instancia = flatpickr(campoResumen, configuracion);

      campoResumen.dataset.fpRangeInitialized = '1';

      campoResumen.addEventListener('keydown', (evento) => {
        if (evento.key === 'Backspace' || evento.key === 'Delete') {
          evento.preventDefault();
          if (instancia) {
            instancia.clear();
          }
          campoInicio.value = '';
          campoFin.value = '';
          campoResumen.value = '';
        }
      });
    });
  };

  document.addEventListener('DOMContentLoaded', () => {
    configurarFlatpickr('.flatpickr-input');
    configurarFlatpickrRango('.flatpickr-range-input');
  });
})();
