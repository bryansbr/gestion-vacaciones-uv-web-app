document.addEventListener('DOMContentLoaded', function () {
  try {
    const params = new URLSearchParams(window.location.search);
    if (params.get('creado') === '1') {
      const codigo = (params.get('codigo') || '').trim();
      const titulo = codigo
        ? `¡El reintegro <strong>${codigo}</strong> fue creado exitosamente!`
        : '¡El reintegro fue creado exitosamente!';
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
