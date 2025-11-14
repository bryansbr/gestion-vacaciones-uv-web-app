document.addEventListener('click', function (e) {
  const btn = e.target.closest('.btn-autorizar-rrhh');
  if (!btn) return;

  const formulario = btn.closest('.form-autorizar-solicitud-rrhh');
  if (!formulario) return;

  e.preventDefault();

  const codigo = formulario.dataset.codigo || '';

  Swal.fire({
    title: "¿Está seguro de autorizar la solicitud de vacaciones?",
    html: `Una vez autorizada, la solicitud <strong>${codigo}</strong> quedará oficialmente aprobada. El funcionario saldrá a vacaciones y se realizará el pago correspondiente.`,
    icon: "question",
    showCancelButton: true,
    confirmButtonColor: "#10b981",
    cancelButtonColor: "#6b7280",
    confirmButtonText: "Sí, autorizar",
    cancelButtonText: "Cancelar",
    input: 'textarea',
    inputPlaceholder: 'Observaciones (obligatorio)',
    inputAttributes: {
      'aria-label': 'Observaciones'
    },
    inputValidator: (value) => {
      return new Promise((resolve) => {
        if (!value || !value.trim()) {
          resolve('Debe proporcionar observaciones');
        } else {
          resolve();
        }
      });
    }
  }).then((resultado) => {
    if (resultado.isConfirmed) {
      const observacion = resultado.value || '';
      if (observacion) {
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
      }
      try { 
        localStorage.setItem('solicitud_autorizada_rrhh', '1');
        localStorage.setItem('solicitud_autorizada_rrhh_codigo', codigo);
      } catch (_) {}
      formulario.submit();
    }
  });
});

document.addEventListener('DOMContentLoaded', function () {
  try {
    const bandera = localStorage.getItem('solicitud_autorizada_rrhh');
    if (bandera === '1') {
      const codigo = localStorage.getItem('solicitud_autorizada_rrhh_codigo') || '';
      localStorage.removeItem('solicitud_autorizada_rrhh');
      localStorage.removeItem('solicitud_autorizada_rrhh_codigo');
      const titulo = codigo 
        ? `¡La solicitud de vacaciones <strong>${codigo}</strong> fue autorizada correctamente!`
        : '¡La solicitud de vacaciones fue autorizada correctamente!';
      Swal.fire({
        position: 'top-end',
        icon: 'success',
        title: titulo,
        html: 'El funcionario saldrá a vacaciones y se realizará el pago correspondiente.',
        showConfirmButton: false,
        timer: 4000
      });
    }
  } catch (_) {}
});
