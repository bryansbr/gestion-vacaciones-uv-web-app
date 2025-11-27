(function() {
  'use strict';

  function inicializarAccionesReintegro() {
    const formEliminar = document.getElementById('form-eliminar-reintegro');

    document.querySelectorAll('.btn-eliminar-reintegro:not([data-accion-inicializada])').forEach((boton) => {
      boton.setAttribute('data-accion-inicializada', 'true');
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

    document.querySelectorAll('.btn-firmar-reintegro:not([data-accion-inicializada])').forEach((boton) => {
      boton.setAttribute('data-accion-inicializada', 'true');
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

    document.querySelectorAll('.btn-enviar-reintegro:not([data-accion-inicializada])').forEach((boton) => {
      boton.setAttribute('data-accion-inicializada', 'true');
      boton.addEventListener('click', function (e) {
        e.preventDefault();
        const form = this.closest('form');
        if (!form) return;
        const codigo = form.dataset.codigo || '';
        const requiereObservacion = form.dataset.requiereObservacion === '1';

        const swalConfig = {
          title: `¿Está seguro de enviar la solicitud de reintegro de vacaciones?`,
          html: requiereObservacion
            ? `Indica las observaciones para reenviar el reintegro <strong>${codigo}</strong>.`
            : `Una vez enviada a su Jefe Inmediato esta acción no se podrá revertir.`,
          icon: 'question',
          showCancelButton: true,
          confirmButtonColor: "#3085d6",
          cancelButtonColor: "#d33",
          confirmButtonText: "Sí, enviar",
          cancelButtonText: "Cancelar"
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
            try {
              localStorage.setItem('reintegro_enviado', codigo);
            } catch (_) {}
            form.submit();
          }
        });
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    inicializarAccionesReintegro();
  });

  window.inicializarAccionesReintegro = inicializarAccionesReintegro;
})();
