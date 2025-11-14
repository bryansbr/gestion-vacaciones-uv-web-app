document.addEventListener('click', function (e) {
  const btn = e.target.closest('.btn-rechazar-rrhh-reintegro');
  if (!btn) return;

  const formulario = btn.closest('.form-rechazar-reintegro-rrhh');
  if (!formulario) return;

  e.preventDefault();

  const codigo = formulario.dataset.codigo || '';

  Swal.fire({
    title: "¿Está seguro de rechazar la solicitud de reintegro de vacaciones?",
    html: `La solicitud <strong>${codigo}</strong> será rechazada definitivamente. Se notificará al Funcionario, su Jefe Inmediato y al Coordinador Administrativo.`,
    icon: "warning",
    showCancelButton: true,
    confirmButtonColor: "#ef4444",
    cancelButtonColor: "#6b7280",
    confirmButtonText: "Sí, rechazar",
    cancelButtonText: "Cancelar",
    input: 'textarea',
    inputPlaceholder: 'Motivo del rechazo (requerido)',
    inputAttributes: {
      'aria-label': 'Motivo del rechazo'
    },
    inputValidator: (value) => {
      if (!value || !value.trim()) {
        return 'Debe proporcionar el motivo del rechazo';
      }
      return null;
    }
  }).then((resultado) => {
    if (resultado.isConfirmed) {
      const observacion = resultado.value || '';
      const inputObs = formulario.querySelector('input[name="obs"]');
      if (inputObs) {
        inputObs.value = observacion;
      } else {
        const hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.name = 'obs';
        hiddenInput.value = observacion;
        formulario.appendChild(hiddenInput);
      }
      try { 
        localStorage.setItem('reintegro_rechazado_rrhh', '1');
        localStorage.setItem('reintegro_rechazado_rrhh_codigo', codigo);
      } catch (_) {}
      formulario.submit();
    }
  });
});

document.addEventListener('DOMContentLoaded', function () {
  try {
    const bandera = localStorage.getItem('reintegro_rechazado_rrhh');
    if (bandera === '1') {
      const codigo = localStorage.getItem('reintegro_rechazado_rrhh_codigo') || '';
      localStorage.removeItem('reintegro_rechazado_rrhh');
      localStorage.removeItem('reintegro_rechazado_rrhh_codigo');
      const titulo = codigo 
        ? `El reintegro de vacaciones <strong>${codigo}</strong> fue rechazado. Se notificó a todas las partes involucradas.`
        : 'El reintegro de vacaciones fue rechazado. Se notificó a todas las partes involucradas.';
      Swal.fire({
        position: 'top-end',
        icon: 'warning',
        title: titulo,
        showConfirmButton: false,
        timer: 3000
      });
    }
  } catch (_) {}
});
