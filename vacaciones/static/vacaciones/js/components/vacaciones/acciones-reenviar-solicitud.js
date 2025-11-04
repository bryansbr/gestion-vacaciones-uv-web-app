document.addEventListener('click', function (e) {
  const btn = e.target.closest('.btn-reenviar-solicitud');
  if (!btn) return;

  const formulario = btn.closest('.form-reenviar-solicitud');
  if (!formulario) return;

  e.preventDefault();

  const codigo = formulario.dataset.codigo || '';

  Swal.fire({
    title: "¿Está seguro de enviar la solicitud de vacaciones?",
    html: `La solicitud <strong>${codigo}</strong> será enviada a su Jefe Inmediato para revisión. Esta no podrá ser editada ni eliminada a menos que sea devuelta.`,
    icon: "question",
    showCancelButton: true,
    confirmButtonColor: "#2563eb",
    cancelButtonColor: "#6b7280",
    confirmButtonText: "Sí, enviar",
    cancelButtonText: "Cancelar"
  }).then((resultado) => {
    if (resultado.isConfirmed) {
      try { 
        localStorage.setItem('solicitud_reenviada', '1');
        localStorage.setItem('solicitud_reenviada_codigo', codigo);
      } catch (_) {}
      formulario.submit();
    }
  });
});

document.addEventListener('DOMContentLoaded', function () {
  try {
    const bandera = localStorage.getItem('solicitud_reenviada');
    if (bandera === '1') {
      const codigo = localStorage.getItem('solicitud_reenviada_codigo') || '';
      localStorage.removeItem('solicitud_reenviada');
      localStorage.removeItem('solicitud_reenviada_codigo');
      const titulo = codigo 
        ? `¡La solicitud de vacaciones <strong>${codigo}</strong> fue enviada exitosamente al Jefe Inmediato!`
        : '¡La solicitud de vacaciones fue enviada exitosamente al Jefe Inmediato!';
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
