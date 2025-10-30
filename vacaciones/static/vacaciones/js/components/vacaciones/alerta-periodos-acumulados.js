document.addEventListener('DOMContentLoaded', function () {
  const marcador = document.getElementById('marcador-alerta-periodos');
  if (!marcador) return;

  Swal.fire({
    title: '¡Atención!',
    text: 'Tiene dos (2) periodos vacacionales acumulados. Debe solicitar primero el más antiguo, de lo contrario, perderá el derecho a este según la normativa vigente.',
    icon: 'warning',
    confirmButtonText: 'Entendido',
    confirmButtonColor: '#3b82f6'
  });
});
