document.addEventListener('DOMContentLoaded', function () {
  const marcador = document.getElementById('marcador-alerta-periodos');
  const botonCrear = document.querySelector('[data-periodos-acumulados="1"]');

  if (!marcador && !botonCrear) return;

  const mostrarAlerta = () => {
    Swal.fire({
      title: '¡Atención!',
      text: 'Tiene dos (2) periodos vacacionales acumulados. Debe solicitar primero el más antiguo, de lo contrario, perderá el derecho a este según la normativa vigente.',
      icon: 'warning',
      confirmButtonText: 'Entendido',
      confirmButtonColor: '#3b82f6'
    });
  };

  if (marcador) {
    mostrarAlerta();
  }

  if (botonCrear) {
    botonCrear.addEventListener('click', mostrarAlerta);
  }
});
