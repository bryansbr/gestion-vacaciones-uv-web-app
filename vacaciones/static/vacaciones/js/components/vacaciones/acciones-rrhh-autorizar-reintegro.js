document.addEventListener('click', function (e) {
  const btn = e.target.closest('.btn-autorizar-rrhh-reintegro');
  if (!btn) return;

  const formulario = btn.closest('.form-autorizar-reintegro-rrhh');
  if (!formulario) return;

  e.preventDefault();

  const codigo = formulario.dataset.codigo || '';

  Swal.fire({
    title: "¿Está seguro de autorizar el reintegro de vacaciones?",
    html: `Una vez autorizada la solicitud <strong>${codigo}</strong>, el funcionario podrá reincorporarse a sus labores en la fecha registrada.`,
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
        localStorage.setItem('reintegro_autorizado_rrhh', '1');
        localStorage.setItem('reintegro_autorizado_rrhh_codigo', codigo);
      } catch (_) {}
      formulario.submit();
    }
  });
});

document.addEventListener('DOMContentLoaded', function () {
  try {
    const bandera = localStorage.getItem('reintegro_autorizado_rrhh');
    if (bandera === '1') {
      const codigo = localStorage.getItem('reintegro_autorizado_rrhh_codigo') || '';
      localStorage.removeItem('reintegro_autorizado_rrhh');
      localStorage.removeItem('reintegro_autorizado_rrhh_codigo');
      const titulo = codigo 
        ? `¡El reintegro de vacaciones <strong>${codigo}</strong> fue autorizado exitosamente!`
        : '¡El reintegro de vacaciones fue autorizado exitosamente!';
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
