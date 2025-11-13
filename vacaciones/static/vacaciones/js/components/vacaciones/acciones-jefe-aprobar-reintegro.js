document.addEventListener('click', function (e) {
  const btn = e.target.closest('.btn-aprobar-reintegro-jefe');
  if (!btn) return;

  const formulario = btn.closest('.form-aprobar-reintegro-jefe');
  if (!formulario) return;

  e.preventDefault();

  const codigo = formulario.dataset.codigo || '';

  Swal.fire({
    title: "¿Está seguro de aprobar el reintegro de vacaciones?",
    html: `Una vez aprobado, el reintegro <strong>${codigo}</strong> será enviado al Coordinador Administrativo para su revisión.`,
    icon: "question",
    showCancelButton: true,
    confirmButtonColor: "#10b981",
    cancelButtonColor: "#6b7280",
    confirmButtonText: "Sí, aprobar",
    cancelButtonText: "Cancelar",
    input: 'textarea',
    inputPlaceholder: 'Observaciones (opcional)',
    inputAttributes: {
      'aria-label': 'Observaciones'
    },
    inputValidator: (value) => {
      return new Promise((resolve) => {
        resolve();
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
        localStorage.setItem('reintegro_aprobado_jefe', '1');
        localStorage.setItem('reintegro_aprobado_jefe_codigo', codigo);
      } catch (_) {}
      formulario.submit();
    }
  });
});

document.addEventListener('DOMContentLoaded', function () {
  try {
    const bandera = localStorage.getItem('reintegro_aprobado_jefe');
    if (bandera === '1') {
      const codigo = localStorage.getItem('reintegro_aprobado_jefe_codigo') || '';
      localStorage.removeItem('reintegro_aprobado_jefe');
      localStorage.removeItem('reintegro_aprobado_jefe_codigo');
      const titulo = codigo 
        ? `¡El reintegro de vacaciones <strong>${codigo}</strong> fue aprobado exitosamente!`
        : '¡El reintegro de vacaciones fue aprobado exitosamente!';
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
