document.addEventListener('click', function (e) {
  const btn = e.target.closest('.btn-devolver-reintegro-coord');
  if (!btn) return;

  const formulario = btn.closest('.form-devolver-reintegro-coord');
  if (!formulario) return;

  e.preventDefault();

  const codigo = formulario.dataset.codigo || '';

  Swal.fire({
    title: "¿Está seguro de devolver la solicitud de reintegro de vacaciones?",
    html: `La solicitud <strong>${codigo}</strong> será devuelta al funcionario para su corrección.`,
    icon: "warning",
    showCancelButton: true,
    confirmButtonColor: "#f59e0b",
    cancelButtonColor: "#6b7280",
    confirmButtonText: "Sí, devolver",
    cancelButtonText: "Cancelar",
    input: 'textarea',
    inputPlaceholder: 'Motivo de la devolución (obligatorio)',
    inputAttributes: {
      'aria-label': 'Motivo de la devolución'
    },
    inputValidator: (value) => {
      return new Promise((resolve) => {
        if (!value || !value.trim()) {
          resolve('Debe indicar el motivo de la devolución');
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
          const ocultarInput = document.createElement('input');
          ocultarInput.type = 'hidden';
          ocultarInput.name = 'obs';
          ocultarInput.value = observacion;
          formulario.appendChild(ocultarInput);
        }
      }
      try { 
        localStorage.setItem('reintegro_devuelto_coord', '1');
        localStorage.setItem('reintegro_devuelto_coord_codigo', codigo);
      } catch (_) {}
      formulario.submit();
    }
  });
});

document.addEventListener('DOMContentLoaded', function () {
  try {
    const bandera = localStorage.getItem('reintegro_devuelto_coord');
    if (bandera === '1') {
      const codigo = localStorage.getItem('reintegro_devuelto_coord_codigo') || '';
      localStorage.removeItem('reintegro_devuelto_coord');
      localStorage.removeItem('reintegro_devuelto_coord_codigo');
      const titulo = codigo 
        ? `El reintegro de vacaciones <strong>${codigo}</strong> fue devuelto exitosamente.`
        : 'El reintegro de vacaciones fue devuelto exitosamente.';
      Swal.fire({
        position: 'top-end',
        icon: 'info',
        title: titulo,
        showConfirmButton: false,
        timer: 2500
      });
    }
  } catch (_) {}
});

