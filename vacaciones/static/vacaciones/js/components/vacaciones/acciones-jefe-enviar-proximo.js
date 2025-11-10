document.addEventListener('click', function (e) {
  const btn = e.target.closest('.btn-enviar-proximo-revisor-jefe');
  if (!btn) return;

  const formulario = btn.closest('.form-enviar-proximo-revisor-jefe');
  if (!formulario) return;

  e.preventDefault();

  const codigo = formulario.dataset.codigo || '';

  Swal.fire({
    title: "¿Está seguro de enviar la solicitud?",
    html: `La solicitud <strong>${codigo}</strong> será enviada al Coordinador Administrativo para su revisión.`,
    icon: "question",
    showCancelButton: true,
    confirmButtonColor: "#2563eb",
    cancelButtonColor: "#6b7280",
    confirmButtonText: "Sí, enviar",
    cancelButtonText: "Cancelar"
  }).then((resultado) => {
    if (resultado.isConfirmed) {
      try { 
        localStorage.setItem('solicitud_enviada_proximo_revisor', '1');
        localStorage.setItem('solicitud_enviada_proximo_revisor_codigo', codigo);
      } catch (_) {}
      formulario.submit();
    }
  });
});

document.addEventListener('DOMContentLoaded', function () {
  try {
    const bandera = localStorage.getItem('solicitud_enviada_proximo_revisor');
    if (bandera === '1') {
      const codigo = localStorage.getItem('solicitud_enviada_proximo_revisor_codigo') || '';
      localStorage.removeItem('solicitud_enviada_proximo_revisor');
      localStorage.removeItem('solicitud_enviada_proximo_revisor_codigo');
      const titulo = codigo 
        ? `¡La solicitud de vacaciones <strong>${codigo}</strong> fue enviada al Coordinador Administrativo exitosamente!`
        : '¡La solicitud de vacaciones fue enviada al Coordinador Administrativo exitosamente!';
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
