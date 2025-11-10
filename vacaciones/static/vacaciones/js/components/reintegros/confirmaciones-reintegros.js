(function () {
  document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('form-reintegro-vacaciones');
    const cancelar = document.getElementById('cancelar-reintegro');
    const guardar = document.getElementById('guardar-reintegro');

    if (!form || typeof Swal === 'undefined') {
      return;
    }

    const modo = form.dataset.mode === 'edit' ? 'edit' : 'create';
    const mensajes = {
      create: {
        titulo: 'Confirmar reintegro',
        texto: '¿Deseas registrar el reintegro de vacaciones?'
      },
      edit: {
        titulo: 'Guardar cambios',
        texto: '¿Deseas guardar los cambios del reintegro?'
      },
      cancelar: {
        titulo: 'Cancelar registro',
        texto: 'Los cambios no se guardarán. ¿Deseas cancelar?'
      }
    };

    if (guardar) {
      guardar.addEventListener('click', function (event) {
        event.preventDefault();
        Swal.fire({
          title: mensajes[modo].titulo,
          text: mensajes[modo].texto,
          icon: 'question',
          showCancelButton: true,
          confirmButtonColor: '#16a34a',
          cancelButtonColor: '#6b7280',
          confirmButtonText: 'Sí, continuar',
          cancelButtonText: 'Cancelar'
        }).then((result) => {
          if (result.isConfirmed) {
            form.submit();
          }
        });
      });
    }

    if (cancelar) {
      cancelar.addEventListener('click', function (event) {
        event.preventDefault();
        Swal.fire({
          title: mensajes.cancelar.titulo,
          text: mensajes.cancelar.texto,
          icon: 'warning',
          showCancelButton: true,
          confirmButtonColor: '#ef4444',
          cancelButtonColor: '#6b7280',
          confirmButtonText: 'Sí, cancelar',
          cancelButtonText: 'Continuar editando'
        }).then((result) => {
          if (result.isConfirmed) {
            window.location.href = cancelar.getAttribute('href');
          }
        });
      });
    }
  });
})();
