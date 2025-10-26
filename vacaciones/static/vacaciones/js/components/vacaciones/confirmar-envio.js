document.addEventListener('click', function (e) {
  const btn = e.target.closest('.btn-enviar-solicitud');
  if (!btn) return;

  const form = btn.closest('.form-enviar-solicitud');
  if (!form) return;

  const codigo = form.dataset.codigo || '';

  // Confirmación
  Swal.fire({
    title: "¿Está seguro de enviar la solicitud de vacaciones?",
    text: "Una vez enviada a su Jefe Inmediato esta acción no se podrá revertir.",
    icon: "warning",
    showCancelButton: true,
    confirmButtonColor: "#3085d6",
    cancelButtonColor: "#d33",
    confirmButtonText: "Sí, enviar",
    cancelButtonText: "Cancelar"
  }).then((result) => {
    if (result.isConfirmed) {
      try { localStorage.setItem('solicitud_enviada', codigo); } catch (_) {}
      form.submit();
    }
  });
});

document.addEventListener('DOMContentLoaded', function () {
  try {
    const codigo = localStorage.getItem('solicitud_enviada');
    if (codigo) {
      localStorage.removeItem('solicitud_enviada');
      Swal.fire({
        title: "¡Solicitud enviada!",
        html: `Tu solicitud de vacaciones <strong>${codigo}</strong> ha sido enviada correctamente.`,
        icon: "success"
      });
    }
  } catch (_) {}
});
