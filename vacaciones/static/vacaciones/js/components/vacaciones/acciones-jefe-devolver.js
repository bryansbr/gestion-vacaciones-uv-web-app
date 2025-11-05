document.addEventListener('click', function (e) {
  const btn = e.target.closest('.btn-devolver-jefe');
  if (!btn) return;

  const formulario = btn.closest('.form-devolver-solicitud-jefe');
  if (!formulario) return;

  e.preventDefault();

  const codigo = formulario.dataset.codigo || '';

  Swal.fire({
    title: "¿Está seguro de devolver la solicitud de vacaciones?",
    html: `La solicitud <strong>${codigo}</strong> será devuelta al funcionario para su corrección.`,
    icon: "warning",
    showCancelButton: true,
    confirmButtonColor: "#eab308",
    cancelButtonColor: "#6b7280",
    confirmButtonText: "Sí, devolver",
    cancelButtonText: "Cancelar",
    input: "textarea",
    inputPlaceholder: "Indique el motivo de la devolución...",
    inputAttributes: {
      'aria-label': 'Motivo de la devolución'
    },
    inputValidator: (value) => {
      if (!value || value.trim() === '') {
        return 'Debe proporcionar un motivo de devolución';
      }
      return null;
    }
  }).then((resultado) => {
    if (resultado.isConfirmed) {
      try { 
        localStorage.setItem('solicitud_devuelta_jefe', '1');
        localStorage.setItem('solicitud_devuelta_jefe_codigo', codigo);
      } catch (_) {}
      const inputHidden = document.createElement('input');
      inputHidden.type = 'hidden';
      inputHidden.name = 'obs';
      inputHidden.value = resultado.value;
      formulario.appendChild(inputHidden);
      formulario.submit();
    }
  });
});

document.addEventListener('DOMContentLoaded', function () {
  try {
    const bandera = localStorage.getItem('solicitud_devuelta_jefe');
    if (bandera === '1') {
      const codigo = localStorage.getItem('solicitud_devuelta_jefe_codigo') || '';
      localStorage.removeItem('solicitud_devuelta_jefe');
      localStorage.removeItem('solicitud_devuelta_jefe_codigo');
      const titulo = codigo 
        ? `La solicitud de vacaciones <strong>${codigo}</strong> fue devuelta exitosamente al funcionario.`
        : 'La solicitud de vacaciones fue devuelta exitosamente al funcionario.';
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
