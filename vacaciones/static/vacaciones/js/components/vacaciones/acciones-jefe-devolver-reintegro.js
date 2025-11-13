document.addEventListener('click', function (e) {
  const btn = e.target.closest('.btn-devolver-reintegro-jefe');
  if (!btn) return;

  const formulario = btn.closest('.form-devolver-reintegro-jefe');
  if (!formulario) return;

  e.preventDefault();

  const codigo = formulario.dataset.codigo || '';

  Swal.fire({
    title: "¿Está seguro de devolver el reintegro de vacaciones?",
    html: `El reintegro <strong>${codigo}</strong> será devuelto al funcionario para su corrección.`,
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
          const hiddenInput = document.createElement('input');
          hiddenInput.type = 'hidden';
          hiddenInput.name = 'obs';
          hiddenInput.value = observacion;
          formulario.appendChild(hiddenInput);
        }
      }
      try { 
        localStorage.setItem('reintegro_devuelto_jefe', '1');
        localStorage.setItem('reintegro_devuelto_jefe_codigo', codigo);
      } catch (_) {}
      formulario.submit();
    }
  });
});

document.addEventListener('DOMContentLoaded', function () {
  try {
    const bandera = localStorage.getItem('reintegro_devuelto_jefe');
    if (bandera === '1') {
      const codigo = localStorage.getItem('reintegro_devuelto_jefe_codigo') || '';
      localStorage.removeItem('reintegro_devuelto_jefe');
      localStorage.removeItem('reintegro_devuelto_jefe_codigo');
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
