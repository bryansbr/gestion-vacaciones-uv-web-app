(function() {
  'use strict';

  document.addEventListener('DOMContentLoaded', function() {
    const menuButtons = document.querySelectorAll('[id^="actions-menu-"]');

    menuButtons.forEach(btn => {
      const solicitudId = btn.id.replace('actions-menu-', '');
      const dropdown = document.getElementById(`dropdown-${solicitudId}`);

      if (!dropdown) return;

      btn.addEventListener('click', function(e) {
        e.stopPropagation();

        const estaAbierto = !dropdown.classList.contains('hidden');

        document.querySelectorAll('[id^="dropdown-"]').forEach(d => {
          d.classList.add('hidden');
          d.classList.remove('bottom-full', 'mb-2');
          d.classList.add('mt-2');
        });

        if (!estaAbierto) {
          const rect = btn.getBoundingClientRect();
          const spaceBelow = window.innerHeight - rect.bottom;
          const spaceAbove = rect.top;
          
          dropdown.classList.remove('hidden');
          
          requestAnimationFrame(function() {
            const originalVisibility = dropdown.style.visibility;
            const originalTop = dropdown.style.top;
            dropdown.style.visibility = 'hidden';
            dropdown.style.top = '-9999px';
            
            const dropdownHeight = dropdown.offsetHeight || 200;
            
            dropdown.style.visibility = originalVisibility;
            dropdown.style.top = originalTop;
            
            if (spaceBelow < dropdownHeight && spaceAbove > spaceBelow) {
              dropdown.classList.remove('mt-2');
              dropdown.classList.add('bottom-full', 'mb-2');
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
        document.querySelectorAll('[id^="dropdown-"]').forEach(d => {
          d.classList.add('hidden');
        });
        document.querySelectorAll('[id^="actions-menu-"]').forEach(btn => {
          btn.setAttribute('aria-expanded', 'false');
        });
      }
    });

    const btnEliminar = document.querySelectorAll('.btn-eliminar-solicitud');
    btnEliminar.forEach(btn => {
      btn.addEventListener('click', function() {
        const url = btn.dataset.url;
        const codigo = btn.dataset.codigo || '';

        Swal.fire({
          title: '¿Está seguro?',
          text: `¿Desea eliminar esta solicitud${codigo ? ` (${codigo})` : ''}?`,
          icon: 'warning',
          showCancelButton: true,
          confirmButtonColor: '#d33',
          cancelButtonColor: '#3085d6',
          confirmButtonText: 'Sí, eliminar',
          cancelButtonText: 'Cancelar'
        }).then((resultado) => {
          if (resultado.isConfirmed) {
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = url;

            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
            if (csrfToken) {
              const csrfInput = document.createElement('input');
              csrfInput.type = 'hidden';
              csrfInput.name = 'csrfmiddlewaretoken';
              csrfInput.value = csrfToken.value;
              form.appendChild(csrfInput);
            }

            document.body.appendChild(form);
            form.submit();
          }
        });
      });
    });
  });
})();
