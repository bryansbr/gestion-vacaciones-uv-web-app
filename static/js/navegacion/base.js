(function() {
  'use strict';

  const botonMenu = document.getElementById('menu-toggle');
  const barraLateral = document.getElementById('sidebar');
  const textosBarraLateral = document.querySelectorAll('.sidebar-text');
  const enlacesBarraLateral = document.querySelectorAll('.sidebar-link');
  let barraLateralColapsada = false;

  if (botonMenu && barraLateral) {
    botonMenu.addEventListener('click', () => {
      barraLateralColapsada = !barraLateralColapsada;
      if (barraLateralColapsada) {
        barraLateral.classList.remove('w-64');
        barraLateral.classList.add('w-16');
        textosBarraLateral.forEach(elemento => elemento.classList.add('hidden'));
        enlacesBarraLateral.forEach(enlace => {
          enlace.classList.remove('gap-2', 'px-3');
          enlace.classList.add('justify-center', 'px-0');
        });
        const submenus = document.querySelectorAll('[id^="submenu-"]');
        submenus.forEach(submenu => {
          if (!submenu.id.includes('-toggle') && !submenu.id.includes('-arrow')) {
            submenu.classList.add('hidden');
          }
        });
      } else {
        barraLateral.classList.remove('w-16');
        barraLateral.classList.add('w-64');
        textosBarraLateral.forEach(elemento => elemento.classList.remove('hidden'));
        enlacesBarraLateral.forEach(enlace => {
          enlace.classList.add('gap-2', 'px-3');
          enlace.classList.remove('justify-center', 'px-0');
        });
      }
    });
  }

  const botonSubmenuToggle = document.getElementById('submenu-solicitudes-toggle');
  const submenu = document.getElementById('submenu-solicitudes');
  const flechaSubmenu = document.getElementById('submenu-solicitudes-arrow');

  if (botonSubmenuToggle && submenu && flechaSubmenu) {
    const rutaActual = window.location.pathname;
    const enlacesSubmenu = submenu.querySelectorAll('a[data-url-path]');
    let tieneItemActivo = false;

    enlacesSubmenu.forEach(enlace => {
      const rutaEnlace = enlace.getAttribute('data-url-path');
      const rutaActualLimpia = rutaActual.split('?')[0];
      const rutaEnlaceLimpia = rutaEnlace.split('?')[0];
      
      if (rutaActualLimpia === rutaEnlaceLimpia || rutaActual.startsWith(rutaEnlaceLimpia)) {
        tieneItemActivo = true;
        enlace.classList.add('bg-red-800', 'font-semibold', 'shadow-md');
        enlace.classList.remove('hover:bg-red-600');
        const icono = enlace.querySelector('svg');
        const texto = enlace.querySelector('.sidebar-text');
        if (icono) icono.classList.add('text-white');
        if (texto) texto.classList.add('text-white');
      }
    });

    if (tieneItemActivo) {
      submenu.classList.remove('hidden');
      flechaSubmenu.classList.add('rotate-180');
    }

    botonSubmenuToggle.addEventListener('click', (e) => {
      e.preventDefault();
      const estaOculto = submenu.classList.contains('hidden');
      
      if (estaOculto) {
        submenu.classList.remove('hidden');
        flechaSubmenu.classList.add('rotate-180');
      } else {
        submenu.classList.add('hidden');
        flechaSubmenu.classList.remove('rotate-180');
      }
    });
  }
})();
