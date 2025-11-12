document.addEventListener('DOMContentLoaded', function () {
  const dropdownButtons = document.querySelectorAll('[id^="reintegro-actions-"]');
  const dropdowns = document.querySelectorAll('[id^="reintegro-dropdown-"]');
  const formEliminar = document.getElementById('form-eliminar-reintegro');

  function cerrarDropdowns(exceptoId) {
    dropdowns.forEach((dropdown) => {
      if (dropdown.id !== exceptoId) {
        dropdown.classList.add('hidden');
      }
    });
  }

  dropdownButtons.forEach((button) => {
    button.addEventListener('click', function (event) {
      event.stopPropagation();
      const targetId = `reintegro-dropdown-${this.id.replace('reintegro-actions-', '')}`;
      const dropdown = document.getElementById(targetId);
      if (!dropdown) return;
      const estabaOculto = dropdown.classList.contains('hidden');
      cerrarDropdowns(targetId);
      if (estabaOculto) {
        dropdown.classList.remove('hidden');
      } else {
        dropdown.classList.add('hidden');
      }
    });
  });

  document.addEventListener('click', function () {
    cerrarDropdowns(null);
  });

  document.querySelectorAll('.btn-eliminar-reintegro').forEach((boton) => {
    boton.addEventListener('click', function (e) {
      e.preventDefault();
      const form = this.closest('form');
      if (!form || !formEliminar) {
        form.submit();
        return;
      }
      const codigo = form.dataset.codigo || '';
      Swal.fire({
        title: 'Confirmar eliminación',
        html: `¿Estás seguro de que deseas eliminar la solicitud de reintegro <strong>${codigo}</strong>?. Esta acción no se puede deshacer.`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#6b7280',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
      }).then((resultado) => {
        if (resultado.isConfirmed) {
          try {
            localStorage.setItem('reintegro_eliminado', '1');
            localStorage.setItem('reintegro_eliminado_codigo', codigo);
          } catch (_) {}
          formEliminar.action = form.action;
          formEliminar.submit();
        }
      });
    });
  });

  document.querySelectorAll('.btn-firmar-reintegro').forEach((boton) => {
    boton.addEventListener('click', function (e) {
      e.preventDefault();
      const form = this.closest('form');
      const codigo = form ? form.dataset.codigo || '' : '';
      Swal.fire({
        title: 'Firmar reintegro',
        html: `¿Deseas firmar digitalmente el reintegro <strong>${codigo}</strong>?`,
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#16a34a',
        cancelButtonColor: '#6b7280',
        confirmButtonText: 'Sí, firmar',
        cancelButtonText: 'Cancelar'
      }).then((resultado) => {
        if (resultado.isConfirmed && form) {
          form.submit();
        }
      });
    });
  });

  document.querySelectorAll('.btn-enviar-reintegro').forEach((boton) => {
    boton.addEventListener('click', function (e) {
      e.preventDefault();
      const form = this.closest('form');
      if (!form) return;
      const codigo = form.dataset.codigo || '';
      const requiereObservacion = form.dataset.requiereObservacion === '1';

      const swalConfig = {
        title: 'Enviar reintegro',
        html: requiereObservacion
          ? `Indica las observaciones para reenviar el reintegro <strong>${codigo}</strong>.`
          : `¿Confirmas el envío del reintegro <strong>${codigo}</strong> al flujo de aprobación?`,
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#2563eb',
        cancelButtonColor: '#6b7280',
        confirmButtonText: 'Enviar',
        cancelButtonText: 'Cancelar'
      };

      if (requiereObservacion) {
        swalConfig.input = 'textarea';
        swalConfig.inputPlaceholder = 'Detalla los ajustes realizados';
        swalConfig.inputValidator = (value) => {
          if (!value || !value.trim()) {
            return 'Debes indicar las observaciones.';
          }
          return null;
        };
      }

      Swal.fire(swalConfig).then((resultado) => {
        if (resultado.isConfirmed) {
          const inputObs = form.querySelector('input[name="obs"]');
          if (requiereObservacion && inputObs) {
            inputObs.value = resultado.value;
          }
          form.submit();
        }
      });
    });
  });
});
