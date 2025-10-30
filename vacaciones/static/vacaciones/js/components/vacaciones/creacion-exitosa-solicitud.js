document.addEventListener('DOMContentLoaded', function () {
  try {
    const bandera = localStorage.getItem('solicitud_creada');
    if (bandera === '1') {
      const codigo = localStorage.getItem('solicitud_creada_codigo') || '';
      localStorage.removeItem('solicitud_creada');
      localStorage.removeItem('solicitud_creada_codigo');
      const titulo = codigo ? `¡La solicitud de vacaciones <strong>${codigo}</strong> se ha creado exitosamente!` : '¡La solicitud de vacaciones fue creada exitosamente!';
      Swal.fire({
        position: "top-end",
        icon: "success",
        title: titulo,
        showConfirmButton: false,
        timer: 2500
      });
    }
  } catch (_) {}
});
