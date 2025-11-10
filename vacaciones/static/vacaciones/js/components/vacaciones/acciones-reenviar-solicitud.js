document.addEventListener('click', function (e) {
  const btn = e.target.closest('.btn-reenviar-solicitud');
  if (!btn) return;

  const formulario = btn.closest('.form-reenviar-solicitud');
  if (!formulario) return;

  e.preventDefault();

  const codigo = formulario.dataset.codigo || '';
  const requiereObservacion = formulario.dataset.requiereObservacion === '1';

  const opciones = {
    icon: "question",
    showCancelButton: true,
    confirmButtonColor: "#2563eb",
    cancelButtonColor: "#6b7280",
    confirmButtonText: "Sí, enviar",
    cancelButtonText: "Cancelar"
  };

  if (requiereObservacion) {
    opciones.title = "Describe los ajustes realizados";
    opciones.html = `La solicitud <strong>${codigo}</strong> fue devuelta para ajustes. Indique brevemente los cambios realizados antes de volver a enviarla.`;
    opciones.input = "textarea";
    opciones.inputPlaceholder = "Detalle los ajustes realizados...";
    opciones.inputAttributes = {
      "aria-label": "Descripción de los ajustes realizados",
      maxlength: 600,
      rows: 4
    };
    opciones.preConfirm = (value) => {
      if (!value || !value.trim()) {
        Swal.showValidationMessage("La descripción es obligatoria para reenviar la solicitud.");
        return false;
      }
      return value.trim();
    };
  } else {
    opciones.title = "¿Está seguro de enviar la solicitud de vacaciones?";
    opciones.html = `La solicitud <strong>${codigo}</strong> será enviada a su Jefe Inmediato para revisión. Esta no podrá ser editada ni eliminada a menos que sea devuelta.`;
  }

  Swal.fire(opciones).then((resultado) => {
    if (resultado.isConfirmed) {
      const observacion = (resultado.value && resultado.value.trim && resultado.value.trim()) || "";
      const obsField = formulario.querySelector('input[name="obs"]');
      if (obsField) {
        obsField.value = observacion;
      } else if (observacion) {
        const hidden = document.createElement('input');
        hidden.type = 'hidden';
        hidden.name = 'obs';
        hidden.value = observacion;
        formulario.appendChild(hidden);
      }

      try { 
        localStorage.setItem('solicitud_reenviada', '1');
        localStorage.setItem('solicitud_reenviada_codigo', codigo);
      } catch (_) {}
      formulario.submit();
    }
  });
});

document.addEventListener('DOMContentLoaded', function () {
  try {
    const bandera = localStorage.getItem('solicitud_reenviada');
    if (bandera === '1') {
      const codigo = localStorage.getItem('solicitud_reenviada_codigo') || '';
      localStorage.removeItem('solicitud_reenviada');
      localStorage.removeItem('solicitud_reenviada_codigo');
      const titulo = codigo 
        ? `¡La solicitud de vacaciones <strong>${codigo}</strong> fue enviada exitosamente al Jefe Inmediato!`
        : '¡La solicitud de vacaciones fue enviada exitosamente al Jefe Inmediato!';
      Swal.fire({
        position: 'top-end',
        icon: 'success',
        title: titulo,
        showConfirmButton: false,
        timer: 2500
      });
    }
  } catch (_) {}
});
