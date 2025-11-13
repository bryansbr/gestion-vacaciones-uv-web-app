document.addEventListener('DOMContentLoaded', function () {
  try {
    const codigo = localStorage.getItem('reintegro_enviado');
    if (codigo) {
      localStorage.removeItem('reintegro_enviado');
      Swal.fire({
        title: "¡Reintegro enviado!",
        html: `Tu reintegro de vacaciones <strong>${codigo}</strong> ha sido enviado correctamente.`,
        icon: "success"
      });
    }
  } catch (_) {}
});
