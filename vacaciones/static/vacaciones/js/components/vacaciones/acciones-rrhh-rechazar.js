document.addEventListener('click', function (e) {
  const btn = e.target.closest('.btn-rechazar-rrhh');
  if (!btn) return;

  const formulario = btn.closest('.form-rechazar-solicitud-rrhh');
  if (!formulario) return;

  e.preventDefault();

  const codigo = formulario.dataset.codigo || '';

  Swal.fire({
    title: "¿Está seguro de rechazar la solicitud de vacaciones?",
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
        localStorage.setItem('solicitud_rechazada_rrhh', '1');
        localStorage.setItem('solicitud_rechazada_rrhh_codigo', codigo);
      } catch (_) {}
      formulario.submit();
    }
  });
});

document.addEventListener('DOMContentLoaded', function () {
  try {
    const bandera = localStorage.getItem('solicitud_rechazada_rrhh');
    if (bandera === '1') {
      const codigo = localStorage.getItem('solicitud_rechazada_rrhh_codigo') || '';
      localStorage.removeItem('solicitud_rechazada_rrhh');
      localStorage.removeItem('solicitud_rechazada_rrhh_codigo');
      const titulo = codigo 
        ? `La solicitud de vacaciones <strong>${codigo}</strong> fue rechazada.`
        : 'La solicitud de vacaciones fue rechazada.';
      Swal.fire({
        position: 'top-end',
        icon: 'warning',
        title: titulo,
        html: 'Se notificó al funcionario, su Jefe Inmediato y al Coordinador Administrativo.',
        showConfirmButton: false,
        timer: 4000
      });
    }
  } catch (_) {}
});
