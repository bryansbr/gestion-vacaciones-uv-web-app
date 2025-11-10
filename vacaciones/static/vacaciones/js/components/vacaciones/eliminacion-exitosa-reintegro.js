document.addEventListener('DOMContentLoaded', function () {
  try {
    const bandera = localStorage.getItem('reintegro_eliminado');
    if (bandera === '1') {
      const codigo = localStorage.getItem('reintegro_eliminado_codigo') || '';
      localStorage.removeItem('reintegro_eliminado');
      localStorage.removeItem('reintegro_eliminado_codigo');
      const titulo = codigo
        ? `¡El reintegro <strong>${codigo}</strong> se ha eliminado correctamente!`
        : '¡El reintegro se ha eliminado correctamente!';
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
