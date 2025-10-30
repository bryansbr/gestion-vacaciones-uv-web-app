document.addEventListener('DOMContentLoaded', function () {
  const link = document.getElementById('cancelar-link');
  if (!link) return;

  link.addEventListener('click', function (e) {
    e.preventDefault();
    Swal.fire({
      title: "¿Está seguro de cancelar?",
      text: "La información de la solicitud se mantendrá como está.",
      icon: "warning",
      showCancelButton: true,
      confirmButtonColor: "#3085d6",
      cancelButtonColor: "#d33",
      confirmButtonText: "Sí, cancelar",
      cancelButtonText: "Volver"
    }).then((r) => {
      if (r.isConfirmed) {
        window.location.href = link.href;
      }
    });
  });
});
