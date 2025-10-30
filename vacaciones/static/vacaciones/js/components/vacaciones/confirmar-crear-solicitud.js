document.addEventListener('DOMContentLoaded', function () {
  const btnEnviar = document.getElementById('submit-btn');
  const formulario = document.querySelector('form[method="post"]');
  
  if (!btnEnviar || !formulario) return;
  
  const formAction = formulario.action || '';
  const textoBtn = btnEnviar.textContent.trim();
  const estaEditando = formAction.includes('/editar/') || textoBtn === 'Guardar cambios';
  
  if (estaEditando) return;
  
  btnEnviar.addEventListener('click', function(e) {
    e.preventDefault();
    
    Swal.fire({
      title: "¿Está seguro de crear la solicitud de vacaciones?",
      text: "Podrá editarla más adelante antes de enviarla a su Jefe Inmediato.",
      icon: "question",
      showCancelButton: true,
      confirmButtonColor: "#3085d6",
      cancelButtonColor: "#d33",
      confirmButtonText: "Sí, crear",
      cancelButtonText: "Cancelar"
    }).then((resultado) => {
      if (resultado.isConfirmed) {
        try {
          localStorage.setItem('solicitud_creada', '1');
          var codigoInput = formulario.querySelector('#id_codigo_sabs') || formulario.querySelector('[name="codigo_sabs"]');
          if (codigoInput && codigoInput.value) {
            localStorage.setItem('solicitud_creada_codigo', String(codigoInput.value));
          }
        } catch (_) {}
        formulario.submit();
      }
    });
  });
});
