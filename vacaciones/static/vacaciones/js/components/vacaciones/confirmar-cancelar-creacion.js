document.addEventListener('DOMContentLoaded', function () {
  const btnCancelar = document.getElementById('cancelar-solicitud');
  if (!btnCancelar) return;

  btnCancelar.addEventListener('click', function (e) {
    e.preventDefault();
    const destino = btnCancelar.dataset.redirect || btnCancelar.dataset.href;
    if (!destino) {
      return;
    }

    Swal.fire({
      title: "¿Está seguro de cancelar?",
      text: "Se perderán todos los datos ingresados de la solicitud de vacaciones.",
      icon: "warning",
      showCancelButton: true,
      confirmButtonColor: "#3085d6",
      cancelButtonColor: "#d33",
      confirmButtonText: "Sí, cancelar",
      cancelButtonText: "Volver"
    }).then((r) => {
      if (r.isConfirmed) {
        window.location.href = destino;
      }
    });
  });
});
