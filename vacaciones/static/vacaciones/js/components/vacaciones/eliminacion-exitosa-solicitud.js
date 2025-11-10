document.addEventListener('DOMContentLoaded', function () {
  try {
    const bandera = localStorage.getItem('solicitud_eliminada');
    if (bandera === '1') {
      const codigo = localStorage.getItem('solicitud_eliminada_codigo') || '';
      localStorage.removeItem('solicitud_eliminada');
      localStorage.removeItem('solicitud_eliminada_codigo');
      const titulo = codigo ? `¡La solicitud de vacaciones <strong>${codigo}</strong> se ha eliminado exitosamente!` : '¡La solicitud de vacaciones se ha eliminado exitosamente!';
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
