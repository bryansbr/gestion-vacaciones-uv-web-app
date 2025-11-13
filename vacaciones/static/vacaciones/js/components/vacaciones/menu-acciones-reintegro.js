(function() {
  'use strict';

  document.addEventListener('DOMContentLoaded', function() {
    const btnsMenu = document.querySelectorAll('[id^="reintegro-actions-"]');

    btnsMenu.forEach(btn => {
      const idReintegro = btn.id.replace('reintegro-actions-', '');
      const desplegable = document.getElementById(`reintegro-dropdown-${idReintegro}`);

      if (!desplegable) return;

      btn.addEventListener('click', function(e) {
        e.stopPropagation();

        const estaAbierto = !desplegable.classList.contains('hidden');

        document.querySelectorAll('[id^="reintegro-dropdown-"]').forEach(menuDesplegable => {
          menuDesplegable.classList.add('hidden');
          menuDesplegable.classList.remove('bottom-full', 'mb-2');
          menuDesplegable.classList.add('mt-2');
        });

        if (!estaAbierto) {
          desplegable.classList.remove('hidden');
          
          requestAnimationFrame(function() {
            const posicion = btn.getBoundingClientRect();
            const alturaDesplegable = desplegable.offsetHeight || 200;
            const espacioAbajo = window.innerHeight - posicion.bottom;
            const espacioArriba = posicion.top;
            const anchoDesplegable = desplegable.offsetWidth || 176; // w-44 = 176px
            
            desplegable.style.position = 'fixed';
            desplegable.style.zIndex = '9999';
            
            const posicionX = posicion.right - anchoDesplegable;
            desplegable.style.left = posicionX + 'px';
            
            if (espacioAbajo < alturaDesplegable && espacioArriba > espacioAbajo) {
              desplegable.style.top = (posicion.top - alturaDesplegable - 8) + 'px';
              desplegable.style.bottom = 'auto';
            } else {
              desplegable.style.top = (posicion.bottom + 8) + 'px';
              desplegable.style.bottom = 'auto';
            }
            
            if (posicionX < 0) {
              desplegable.style.left = '8px';
            }
            
            const topCalculado = parseFloat(desplegable.style.top);
            if (topCalculado + alturaDesplegable > window.innerHeight) {
              desplegable.style.top = (window.innerHeight - alturaDesplegable - 8) + 'px';
            }
            if (topCalculado < 0) {
              desplegable.style.top = '8px';
            }
          });
          
          btn.setAttribute('aria-expanded', 'true');
        } else {
          btn.setAttribute('aria-expanded', 'false');
        }
      });
    });

    document.addEventListener('click', function(e) {
      if (!e.target.closest('[id^="reintegro-actions-"]') && !e.target.closest('[id^="reintegro-dropdown-"]')) {
        document.querySelectorAll('[id^="reintegro-dropdown-"]').forEach(menuDesplegable => {
          menuDesplegable.classList.add('hidden');
        });
        document.querySelectorAll('[id^="reintegro-actions-"]').forEach(btn => {
          btn.setAttribute('aria-expanded', 'false');
        });
      }
    });
  });
})();
