document.addEventListener('click', function (e) {
  const btn = e.target.closest('.btn-devolver-coord');
  if (!btn) return;

  const formulario = btn.closest('.form-devolver-solicitud-coord');
  if (!formulario) return;

  e.preventDefault();

  const codigo = formulario.dataset.codigo || '';

  Swal.fire({
    title: "¿Está seguro de devolver la solicitud?",
    html: `La solicitud <strong>${codigo}</strong> será devuelta al funcionario con las observaciones que proporcione.`,
    icon: "warning",
    showCancelButton: true,
    confirmButtonColor: "#ef4444",
    cancelButtonColor: "#6b7280",
    confirmButtonText: "Sí, devolver",
    cancelButtonText: "Cancelar",
    input: 'textarea',
    inputPlaceholder: 'Motivo de la devolución (requerido)',
    inputAttributes: {
      'aria-label': 'Motivo de la devolución'
    },
    inputValidator: (value) => {
      if (!value || !value.trim()) {
        return 'Debe proporcionar el motivo de la devolución';
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
        localStorage.setItem('solicitud_devuelta_coord', '1');
        localStorage.setItem('solicitud_devuelta_coord_codigo', codigo);
      } catch (_) {}
      formulario.submit();
    }
  });
});

document.addEventListener('DOMContentLoaded', function () {
  try {
    const bandera = localStorage.getItem('solicitud_devuelta_coord');
    if (bandera === '1') {
      const codigo = localStorage.getItem('solicitud_devuelta_coord_codigo') || '';
      localStorage.removeItem('solicitud_devuelta_coord');
      localStorage.removeItem('solicitud_devuelta_coord_codigo');
      const titulo = codigo 
        ? `La solicitud de vacaciones <strong>${codigo}</strong> fue devuelta al funcionario con observaciones.`
        : 'La solicitud de vacaciones fue devuelta al funcionario con observaciones.';
      Swal.fire({
        position: 'top-end',
        icon: 'info',
        title: titulo,
        showConfirmButton: false,
        timer: 3000
      });
    }
  } catch (_) {}
});
