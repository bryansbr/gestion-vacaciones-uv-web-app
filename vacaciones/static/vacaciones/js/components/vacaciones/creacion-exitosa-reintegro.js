document.addEventListener('DOMContentLoaded', function () {
  try {
    const params = new URLSearchParams(window.location.search);
    if (params.get('creado') === '1') {
      const codigo = (params.get('codigo') || '').trim();
      const titulo = codigo
        ? `¡La solicitud de reintegro <strong>${codigo}</strong> fue creada exitosamente!`
        : '¡La solicitud de reintegro fue creada exitosamente!';
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
