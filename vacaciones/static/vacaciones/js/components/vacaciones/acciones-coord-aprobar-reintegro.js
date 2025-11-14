document.addEventListener('click', function (e) {
  const btn = e.target.closest('.btn-aprobar-reintegro-coord');
  if (!btn) return;

  const formulario = btn.closest('.form-aprobar-reintegro-coord');
  if (!formulario) return;

  e.preventDefault();

  const codigo = formulario.dataset.codigo || '';

  Swal.fire({
    title: "¿Está seguro de aprobar la solicitud de reintegro de vacaciones?",
    html: `Una vez aprobada, la solicitud <strong>${codigo}</strong> será enviada a Recursos Humanos para su autorización final.`,
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
    }
  }).then((resultado) => {
    if (resultado.isConfirmed) {
      const observacion = resultado.value || '';
      if (observacion) {
        const inputObs = formulario.querySelector('input[name="obs"]');
        if (inputObs) {
          inputObs.value = observacion;
        } else {
          const ocultarInput = document.createElement('input');
          ocultarInput.type = 'hidden';
          ocultarInput.name = 'obs';
          ocultarInput.value = observacion;
          formulario.appendChild(ocultarInput);
        }
      }
      try { 
        localStorage.setItem('reintegro_aprobado_coord', '1');
        localStorage.setItem('reintegro_aprobado_coord_codigo', codigo);
      } catch (_) {}
      formulario.submit();
    }
  });
});

document.addEventListener('DOMContentLoaded', function () {
  try {
    const bandera = localStorage.getItem('reintegro_aprobado_coord');
    if (bandera === '1') {
      const codigo = localStorage.getItem('reintegro_aprobado_coord_codigo') || '';
      localStorage.removeItem('reintegro_aprobado_coord');
      localStorage.removeItem('reintegro_aprobado_coord_codigo');
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
