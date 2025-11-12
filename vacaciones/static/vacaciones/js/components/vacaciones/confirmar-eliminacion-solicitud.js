document.addEventListener('DOMContentLoaded', function () {
  const contenedor = document.getElementById('delete-page');
  const formulario = document.getElementById('delete-form');
  if (!contenedor || !formulario) return;

  const codigo = contenedor.getAttribute('data-codigo') || '';
  const urlAnterior = contenedor.getAttribute('data-back-url') || '/';

  Swal.fire({
    title: 'Confirmar eliminación',
    html: `¿Estás seguro de que deseas eliminar la solicitud de vacaciones <strong>${codigo}</strong>?. Esta acción no se puede deshacer.`,
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#d33',
    cancelButtonColor: '#6b7280',
    confirmButtonText: 'Sí, eliminar',
    cancelButtonText: 'Cancelar'
  }).then((resultado) => {
    if (resultado.isConfirmed) {
      try {
        localStorage.setItem('solicitud_eliminada', '1');
        localStorage.setItem('solicitud_eliminada_codigo', codigo);
      } catch (_) {}
      formulario.submit();
    } else {
      window.location.href = urlAnterior;
    }
  });
});
