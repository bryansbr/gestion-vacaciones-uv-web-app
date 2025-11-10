document.addEventListener('DOMContentLoaded', function () {
  try {
    const parametros = new URLSearchParams(window.location.search);
    if (parametros.get('actualizada') === '1') {
      const codigo = (parametros.get('codigo') || '').trim();
      const titulo = codigo
        ? `¡La solicitud de vacaciones <strong>${codigo}</strong> fue actualizada exitosamente!`
        : '¡La solicitud de vacaciones fue actualizada exitosamente!';
      Swal.fire({
        position: "top-end",
        icon: "success",
        title: titulo,
        showConfirmButton: false,
        timer: 2500
      });
    }
  } catch (_) {}
});
