document.addEventListener('DOMContentLoaded', function () {
  const btnEnviar = document.getElementById('submit-btn');
  const formulario = document.querySelector('form[method="post"]');
  
  if (!btnEnviar || !formulario) return;
  
  const formAction = formulario.action || '';
  const textoBtn = btnEnviar.textContent.trim();
  const estaEditando = formAction.includes('/editar/') || textoBtn === 'Guardar cambios';
  
  btnEnviar.addEventListener('click', function(e) {
    e.preventDefault();
    
    if (estaEditando) {
      Swal.fire({
        title: "¿Está seguro de guardar los cambios?",
        text: "Se actualizará la información de la solicitud de vacaciones.",
        icon: "question",
        showCancelButton: true,
        confirmButtonColor: "#3085d6",
        cancelButtonColor: "#6b7280",
        confirmButtonText: "Sí, guardar",
        cancelButtonText: "Cancelar"
      }).then((resultado) => {
        if (resultado.isConfirmed) {
          formulario.submit();
        }
      });
    } else {
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
          formulario.submit();
        }
      });
    }
  });
});
