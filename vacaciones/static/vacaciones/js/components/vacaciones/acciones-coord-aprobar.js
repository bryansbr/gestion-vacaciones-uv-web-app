document.addEventListener('click', function (e) {
  const btn = e.target.closest('.btn-aprobar-coord');
  if (!btn) return;

  const formulario = btn.closest('.form-aprobar-solicitud-coord');
  if (!formulario) return;

  e.preventDefault();

  const codigo = formulario.dataset.codigo || '';

  Swal.fire({
    title: "¿Está seguro de aprobar la solicitud de vacaciones?",
    html: `Una vez aprobada, la solicitud <strong>${codigo}</strong> será enviada a la División de Recursos Humanos para su revisión final.`,
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
        localStorage.setItem('solicitud_aprobada_coord', '1');
        localStorage.setItem('solicitud_aprobada_coord_codigo', codigo);
      } catch (_) {}
      formulario.submit();
    }
  });
});

document.addEventListener('DOMContentLoaded', function () {
  try {
    const bandera = localStorage.getItem('solicitud_aprobada_coord');
    if (bandera === '1') {
      const codigo = localStorage.getItem('solicitud_aprobada_coord_codigo') || '';
      localStorage.removeItem('solicitud_aprobada_coord');
      localStorage.removeItem('solicitud_aprobada_coord_codigo');
      const titulo = codigo 
        ? `¡La solicitud de vacaciones <strong>${codigo}</strong> fue aprobada exitosamente!`
        : '¡La solicitud de vacaciones fue aprobada exitosamente!';
      Swal.fire({
        position: 'top-end',
        icon: 'success',
        title: titulo,
        html: 'Se ha enviado a Recursos Humanos.',
        showConfirmButton: false,
        timer: 3000
      });
    }
  } catch (_) {}
});
