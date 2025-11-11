(function () {
  document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('form-reintegro-vacaciones');
    const cancelar = document.getElementById('cancelar-reintegro');
    const crearSolicitud = document.getElementById('crear-solicitud');
    const motivoField = document.getElementById('id_motivo_reintegro');
    const observacionesField = document.getElementById('id_observaciones');
    const numericDefaults = form ? Array.from(form.querySelectorAll('[data-default-zero="true"]')) : [];

    if (!form || typeof Swal === 'undefined') {
      return;
    }

    const modo = form.dataset.mode === 'edit' ? 'edit' : 'create';
    const mensajes = {
      create: {
        titulo: 'Confirmar creación',
        texto: '¿Deseas crear la solicitud de reintegro de vacaciones?'
      },
      edit: {
        titulo: 'Guardar cambios',
        texto: '¿Deseas guardar los cambios del reintegro?'
      },
      cancelar: {
        titulo: '¿Está seguro de cancelar?',
        texto: 'Se perderán todos los datos ingresados del reintegro de vacaciones.'
      }
    };

    const observacionesObligatorias = () => {
      if (!motivoField) {
        return false;
      }
      return motivoField.value === 'suspension_anticipada';
    };

    const actualizarRequerimientoObservaciones = () => {
      if (!observacionesField) {
        return;
      }
      if (observacionesObligatorias()) {
        observacionesField.setAttribute('required', 'required');
      } else {
        observacionesField.removeAttribute('required');
      }
    };

    const limpiarErroresPrevios = () => {
      const errores = form.querySelectorAll('.input-error');
      errores.forEach((el) => {
        el.classList.remove('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');
      });
      const mensajes = form.querySelectorAll('[data-error-message="true"]');
      mensajes.forEach((mensaje) => {
        mensaje.remove();
      });
    };

    const marcarCampoInvalido = (campo, mensaje) => {
      if (!campo) {
        return;
      }

      campo.classList.add('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');
      campo.classList.add('input-error');

      const contenedor = campo.closest('.mb-4') || campo.parentElement;
      if (!contenedor) {
        return;
      }

      const mensajeExistente = contenedor.querySelector('[data-error-message="true"]');
      if (mensajeExistente) {
        mensajeExistente.textContent = mensaje;
        return;
      }

      const errorEl = document.createElement('p');
      errorEl.textContent = mensaje;
      errorEl.dataset.errorMessage = 'true';
      errorEl.className = 'text-sm text-red-600 mt-1';
      contenedor.appendChild(errorEl);
    };

    const obtenerCamposObligatorios = () => {
      const campos = Array.from(form.querySelectorAll('input, select, textarea'));
      return campos.filter((campo) => {
        if (campo.type === 'hidden' || campo.disabled) {
          return false;
        }
        if (campo.name === 'csrfmiddlewaretoken') {
          return false;
        }
        if (campo === observacionesField && !observacionesObligatorias()) {
          return false;
        }
        return true;
      });
    };

    const obtenerCamposVacios = () => {
      const campos = obtenerCamposObligatorios();
      return campos.filter((campo) => {
        if (campo.type === 'checkbox' || campo.type === 'radio') {
          return !campo.checked;
        }
        const valor = (campo.value || '').trim();
        return valor === '';
      });
    };

    actualizarRequerimientoObservaciones();
    if (motivoField) {
      motivoField.addEventListener('change', actualizarRequerimientoObservaciones);
    }

    const restablecerSiVacio = (campo) => {
      const valor = (campo.value || '').trim();
      if (valor === '') {
        campo.value = '0';
      }
    };

    numericDefaults.forEach((campo) => {
      campo.addEventListener('focus', () => {
        if (campo.value === '0') {
          campo.value = '';
        }
      });

      campo.addEventListener('blur', () => {
        restablecerSiVacio(campo);
      });
    });

    if (crearSolicitud) {
      crearSolicitud.addEventListener('click', function (event) {
        event.preventDefault();

        limpiarErroresPrevios();

        numericDefaults.forEach(restablecerSiVacio);

        const camposVacios = obtenerCamposVacios();
        if (camposVacios.length > 0) {
          camposVacios.forEach((campo) => {
            let mensaje = 'Este campo es obligatorio.';
            if (campo === observacionesField && observacionesObligatorias()) {
              mensaje = 'Las observaciones son obligatorias cuando el motivo es suspensión anticipada por necesidad del servicio.';
            }
            marcarCampoInvalido(campo, mensaje);
          });

          Swal.fire({
            title: 'Campos incompletos',
            text: 'Por favor completa todos los campos obligatorios antes de crear la solicitud.',
            icon: 'warning',
            confirmButtonText: 'Entendido'
          });
          return;
        }

        Swal.fire({
          title: mensajes[modo].titulo,
          text: mensajes[modo].texto,
          icon: 'question',
          showCancelButton: true,
          confirmButtonColor: '#3085d6',
          cancelButtonColor: '#d33',
          confirmButtonText: 'Sí, continuar',
          cancelButtonText: 'Cancelar'
        }).then((result) => {
          if (result.isConfirmed) {
            form.submit();
          }
        });
      });
    }

    if (cancelar) {
      cancelar.addEventListener('click', function (event) {
        event.preventDefault();
        Swal.fire({
          title: mensajes.cancelar.titulo,
          text: mensajes.cancelar.texto,
          icon: 'warning',
          showCancelButton: true,
          confirmButtonColor: '#3085d6',
          cancelButtonColor: '#d33',
          confirmButtonText: 'Sí, cancelar',
          cancelButtonText: 'Volver'
        }).then((result) => {
          if (result.isConfirmed) {
            window.location.href = form.getAttribute('action') || cancelar.dataset.redirect;
          }
        });
      });
    }
  });
})();
