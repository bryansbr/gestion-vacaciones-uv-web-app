document.addEventListener('DOMContentLoaded', function () {
  const btnAccion = document.getElementById('crear-solicitud-vacaciones');
  const btnOculto = document.getElementById('submit-btn');
  const formulario = document.querySelector('form[method="post"]');

  if (!btnAccion || !btnOculto || !formulario || typeof Swal === 'undefined') {
    return;
  }

  const modo = formulario.dataset.mode === 'edit' ? 'edit' : 'create';
  const mensajes = {
    create: {
      titulo: '¿Está seguro de crear la solicitud de vacaciones?',
      texto: 'Podrá editarla más adelante antes de enviarla a su Jefe Inmediato.'
    },
    edit: {
      titulo: '¿Está seguro de guardar los cambios?',
      texto: 'Se actualizará la información de la solicitud de vacaciones.'
    }
  };

  const limpiarErroresPrevios = () => {
    const camposConError = formulario.querySelectorAll('.input-error');
    camposConError.forEach((campo) => {
      campo.classList.remove('border-red-500', 'focus:border-red-500', 'focus:ring-red-500', 'input-error');
    });

    const mensajesError = formulario.querySelectorAll('[data-error-message="true"]');
    mensajesError.forEach((mensaje) => mensaje.remove());
  };

  const obtenerTextoCampo = (campo) => {
    const etiqueta = formulario.querySelector(`label[for="${campo.id}"]`);
    if (etiqueta) {
      return etiqueta.textContent.replace('*', '').trim();
    }
    return 'Este campo';
  };

  const marcarCampoInvalido = (campo, mensaje) => {
    campo.classList.add('border-red-500', 'focus:border-red-500', 'focus:ring-red-500', 'input-error');

    const contenedor = campo.closest('.mb-4') || campo.parentElement;
    if (!contenedor) {
      return;
    }

    const existente = contenedor.querySelector('[data-error-message="true"]');
    if (existente) {
      existente.textContent = mensaje;
      return;
    }

    const parrafoError = document.createElement('p');
    parrafoError.dataset.errorMessage = 'true';
    parrafoError.className = 'text-sm text-red-600 mt-1';
    parrafoError.textContent = mensaje;
    contenedor.appendChild(parrafoError);
  };

  const esCampoObligatorio = (campo) => {
    if (campo.required) {
      return true;
    }

    const camposAdicionales = ['id_periodo_vacacional', 'id_fecha_inicio_vacaciones', 'id_fecha_fin_vacaciones'];
    return camposAdicionales.includes(campo.id);
  };

  const obtenerCamposObligatorios = () => {
    const campos = Array.from(formulario.querySelectorAll('input, select, textarea'));
    return campos.filter((campo) => {
      if (campo.type === 'hidden' || campo.disabled) {
        return false;
      }
      if (campo.name === 'csrfmiddlewaretoken') {
        return false;
      }
      if (campo === btnAccion || campo === btnOculto) {
        return false;
      }
      return esCampoObligatorio(campo);
    });
  };

  const obtenerCamposVacios = () => {
    const camposObligatorios = obtenerCamposObligatorios();
    return camposObligatorios.filter((campo) => {
      if (campo.type === 'checkbox' || campo.type === 'radio') {
        return !campo.checked;
      }
      const valor = (campo.value || '').trim();
      return valor === '';
    });
  };

  btnAccion.addEventListener('click', function (event) {
    event.preventDefault();
    limpiarErroresPrevios();

    const camposVacios = obtenerCamposVacios();
    if (camposVacios.length > 0) {
      camposVacios.forEach((campo) => {
        const textoCampo = obtenerTextoCampo(campo);
        const mensaje = `${textoCampo} es obligatorio.`;
        marcarCampoInvalido(campo, mensaje);
      });

      Swal.fire({
        title: 'Campos incompletos',
        text: 'Por favor completa todos los campos obligatorios antes de continuar.',
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
      cancelButtonColor: '#6b7280',
      confirmButtonText: modo === 'edit' ? 'Sí, guardar' : 'Sí, crear',
      cancelButtonText: 'Cancelar'
    }).then((resultado) => {
      if (resultado.isConfirmed) {
        if (typeof formulario.requestSubmit === 'function') {
          formulario.requestSubmit(btnOculto);
        } else {
          btnOculto.disabled = false;
          formulario.submit();
        }
      }
    });
  });
});
