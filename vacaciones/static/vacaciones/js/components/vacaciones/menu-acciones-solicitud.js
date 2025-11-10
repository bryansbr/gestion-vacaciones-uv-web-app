(function() {
  'use strict';

  document.addEventListener('DOMContentLoaded', function() {
    const btnsMenu = document.querySelectorAll('[id^="actions-menu-"]');

    btnsMenu.forEach(btn => {
      const idSolicitud = btn.id.replace('actions-menu-', '');
      const desplegable = document.getElementById(`dropdown-${idSolicitud}`);

      if (!desplegable) return;

      btn.addEventListener('click', function(e) {
        e.stopPropagation();

        const estaAbierto = !desplegable.classList.contains('hidden');

        document.querySelectorAll('[id^="dropdown-"]').forEach(menuDesplegable => {
          menuDesplegable.classList.add('hidden');
          menuDesplegable.classList.remove('bottom-full', 'mb-2');
          menuDesplegable.classList.add('mt-2');
        });

        if (!estaAbierto) {
          desplegable.classList.remove('hidden');
          
          requestAnimationFrame(function() {
            const posicion = btn.getBoundingClientRect();
            const posicionDesplegable = desplegable.getBoundingClientRect();
            const alturaDesplegable = posicionDesplegable.height || desplegable.offsetHeight || 200;
            const espacioAbajo = window.innerHeight - posicion.bottom;
            const espacioArriba = posicion.top;
            
            if (espacioAbajo < alturaDesplegable && espacioArriba > espacioAbajo) {
              desplegable.classList.remove('mt-2');
              desplegable.classList.add('bottom-full', 'mb-2');
            } else {
              desplegable.classList.remove('bottom-full', 'mb-2');
              desplegable.classList.add('mt-2');
            }
          });
          
          btn.setAttribute('aria-expanded', 'true');
        } else {
          btn.setAttribute('aria-expanded', 'false');
        }
      });
    });

    document.addEventListener('click', function(e) {
      if (!e.target.closest('[id^="actions-menu-"]') && !e.target.closest('[id^="dropdown-"]')) {
        document.querySelectorAll('[id^="dropdown-"]').forEach(menuDesplegable => {
          menuDesplegable.classList.add('hidden');
        });
        document.querySelectorAll('[id^="actions-menu-"]').forEach(btn => {
          btn.setAttribute('aria-expanded', 'false');
        });
      }
    });

    const btnEliminar = document.querySelectorAll('.btn-eliminar-solicitud');
    btnEliminar.forEach(btn => {
      btn.addEventListener('click', function() {
        const urlEliminar = btn.dataset.url;
        const codigo = btn.dataset.codigo || '';

        Swal.fire({
          title: '¿Está seguro?',
          html: codigo 
            ? `Está a punto de eliminar la solicitud <strong>${codigo}</strong>. La acción no se podrá deshacer.`
            : 'Está a punto de eliminar la solicitud. La acción no se podrá deshacer.',
          icon: 'warning',
          showCancelButton: true,
          confirmButtonColor: '#d33',
          cancelButtonColor: '#3085d6',
          confirmButtonText: 'Sí, eliminar',
          cancelButtonText: 'Cancelar'
        }).then((resultado) => {
          if (resultado.isConfirmed) {
            const formulario = document.createElement('form');
            formulario.method = 'POST';
            formulario.action = urlEliminar;

            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
            if (csrfToken) {
              const csrfInput = document.createElement('input');
              csrfInput.type = 'hidden';
              csrfInput.name = 'csrfmiddlewaretoken';
              csrfInput.value = csrfToken.value;
              formulario.appendChild(csrfInput);
            }

            document.body.appendChild(formulario);
            formulario.submit();
          }
        });
      });
    });
  });
})();
