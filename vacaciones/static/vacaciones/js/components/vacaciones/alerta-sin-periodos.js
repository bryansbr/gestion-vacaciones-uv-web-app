document.addEventListener('DOMContentLoaded', function () {
  const btnCrearSinPeriodos = document.getElementById('btn-crear-sin-periodos');
  
  if (btnCrearSinPeriodos) {
    btnCrearSinPeriodos.addEventListener('click', function(e) {
      e.preventDefault();
      Swal.fire({
        icon: "error",
        title: "¡Atención!",
        text: "No puede solicitar vacaciones porque no tiene periodos registrados. Contacte al administrador para que registre su(s) periodo(s) vacacional(es).",
      });
    });
  }
});

