document.addEventListener('click', function (e) {
  const btn = e.target.closest('.btn-aprobar-jefe');
  if (!btn) return;

  const formulario = btn.closest('.form-aprobar-solicitud-jefe');
  if (!formulario) return;

  e.preventDefault();

  const codigo = formulario.dataset.codigo || '';

  Swal.fire({
    title: "¿Está seguro de aprobar la solicitud de vacaciones?",
    html: `Una vez aprobada, la solicitud <strong>${codigo}</strong> será enviada al Coordinador Administrativo para su revisión.`,
    icon: "question",
    showCancelButton: true,
    confirmButtonColor: "#10b981",
    cancelButtonColor: "#6b7280",
    confirmButtonText: "Sí, aprobar",
    cancelButtonText: "Cancelar"
  }).then((resultado) => {
    if (resultado.isConfirmed) {
      try { 
        localStorage.setItem('solicitud_aprobada_jefe', '1');
        localStorage.setItem('solicitud_aprobada_jefe_codigo', codigo);
      } catch (_) {}
      formulario.submit();
    }
  });
});

document.addEventListener('DOMContentLoaded', function () {
  try {
    const bandera = localStorage.getItem('solicitud_aprobada_jefe');
    if (bandera === '1') {
      const codigo = localStorage.getItem('solicitud_aprobada_jefe_codigo') || '';
      localStorage.removeItem('solicitud_aprobada_jefe');
      localStorage.removeItem('solicitud_aprobada_jefe_codigo');
      const titulo = codigo 
        ? `¡La solicitud de vacaciones <strong>${codigo}</strong> fue aprobada exitosamente!`
        : '¡La solicitud de vacaciones fue aprobada exitosamente!';
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

