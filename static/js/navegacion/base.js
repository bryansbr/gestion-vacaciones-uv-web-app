(function() {
  'use strict';

  const btnMenu = document.getElementById('menu-toggle');
  const barraLateral = document.getElementById('sidebar');
  const textosBarraLateral = document.querySelectorAll('.sidebar-text');
  const enlacesBarraLateral = document.querySelectorAll('.sidebar-link');
  let barraLateralColapsada = false;

  if (btnMenu && barraLateral) {
    btnMenu.addEventListener('click', () => {
      barraLateralColapsada = !barraLateralColapsada;
      if (barraLateralColapsada) {
        barraLateral.classList.remove('w-64');
        barraLateral.classList.add('w-16');
        textosBarraLateral.forEach(el => el.classList.add('hidden'));
        enlacesBarraLateral.forEach(a => {
          a.classList.remove('gap-2', 'px-3');
          a.classList.add('justify-center', 'px-0');
        });
        document.querySelectorAll('[id^="submenu-"]').forEach(sub => {
          if (!sub.id.includes('-toggle') && !sub.id.includes('-arrow')) sub.classList.add('hidden');
        });
        document.querySelectorAll('.sidebar-popover').forEach(pop => pop.classList.add('hidden'));
      } else {
        barraLateral.classList.remove('w-16');
        barraLateral.classList.add('w-64');
        textosBarraLateral.forEach(el => el.classList.remove('hidden'));
        enlacesBarraLateral.forEach(a => {
          a.classList.add('gap-2', 'px-3');
          a.classList.remove('justify-center', 'px-0');
        });
      }
    });
  }

  const btnSubmenuToggle = document.getElementById('submenu-solicitudes-toggle');
  const submenu = document.getElementById('submenu-solicitudes');
  const flechaSubmenu = document.getElementById('submenu-solicitudes-arrow');

  if (btnSubmenuToggle && submenu && flechaSubmenu) {
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

    let ocultarTimeoutMain = null;

    const mostrarMain = () => {
      if (ocultarTimeoutMain) {
        clearTimeout(ocultarTimeoutMain);
        ocultarTimeoutMain = null;
      }
      submenu.classList.remove('hidden');
      flechaSubmenu.classList.add('rotate-180');
    };

    const ocultarMain = () => {
      submenu.classList.add('hidden');
      flechaSubmenu.classList.remove('rotate-180');
    };

    const ocultarCalendarioMain = () => {
      ocultarTimeoutMain = window.setTimeout(ocultarMain, 150);
    };

    btnSubmenuToggle.addEventListener('mouseenter', mostrarMain);
    btnSubmenuToggle.addEventListener('mouseleave', ocultarCalendarioMain);
    btnSubmenuToggle.addEventListener('focus', mostrarMain);
    btnSubmenuToggle.addEventListener('blur', ocultarCalendarioMain);

    submenu.addEventListener('mouseenter', mostrarMain);
    submenu.addEventListener('mouseleave', ocultarCalendarioMain);
  }

  const btnSubmenuReintegros = document.getElementById('submenu-reintegros-toggle');
  const submenuReintegros = document.getElementById('submenu-reintegros');
  const flechaReintegros = document.getElementById('submenu-reintegros-arrow');

  if (btnSubmenuReintegros && submenuReintegros && flechaReintegros) {
    const rutaActual = window.location.pathname;
    const enlacesReintegros = submenuReintegros.querySelectorAll('a[data-url-path]');
    let activoReintegros = false;

    enlacesReintegros.forEach(enlace => {
      const rutaEnlace = enlace.getAttribute('data-url-path');
      const caminoActual = rutaActual.split('?')[0];
      const caminoEnlace = (rutaEnlace || '').split('?')[0];

      if (caminoActual === caminoEnlace || rutaActual.startsWith(caminoEnlace)) {
        activoReintegros = true;
        enlace.classList.add('bg-red-800', 'font-semibold', 'shadow-md');
        enlace.classList.remove('hover:bg-red-600');
        const icono = enlace.querySelector('svg');
        const texto = enlace.querySelector('.sidebar-text');
        if (icono) icono.classList.add('text-white');
        if (texto) texto.classList.add('text-white');
      }
    });

    if (activoReintegros) {
      submenuReintegros.classList.remove('hidden');
      flechaReintegros.classList.add('rotate-180');
    }

    let ocultarTimeoutReintegros = null;

    const mostrarReintegros = () => {
      if (ocultarTimeoutReintegros) {
        clearTimeout(ocultarTimeoutReintegros);
        ocultarTimeoutReintegros = null;
      }
      submenuReintegros.classList.remove('hidden');
      flechaReintegros.classList.add('rotate-180');
    };

    const ocultarReintegros = () => {
      submenuReintegros.classList.add('hidden');
      flechaReintegros.classList.remove('rotate-180');
    };

    const programarOcultarReintegros = () => {
      ocultarTimeoutReintegros = window.setTimeout(ocultarReintegros, 150);
    };

    btnSubmenuReintegros.addEventListener('mouseenter', mostrarReintegros);
    btnSubmenuReintegros.addEventListener('mouseleave', programarOcultarReintegros);
    btnSubmenuReintegros.addEventListener('focus', mostrarReintegros);
    btnSubmenuReintegros.addEventListener('blur', programarOcultarReintegros);

    submenuReintegros.addEventListener('mouseenter', mostrarReintegros);
    submenuReintegros.addEventListener('mouseleave', programarOcultarReintegros);
  }

  const btnListadoToggle = document.getElementById('submenu-listado-toggle');
  const submenuListado = document.getElementById('submenu-listado');
  const flechaListado = document.getElementById('submenu-listado-arrow');

  if (btnListadoToggle && submenuListado && flechaListado) {
    const rutaActual = window.location.pathname;
    const enlacesListado = submenuListado.querySelectorAll('a[data-url-path]');
    let activo = false;

    enlacesListado.forEach(enlace => {
      const rutaEnlace = enlace.getAttribute('data-url-path') || '';
      const cur = rutaActual.split('?')[0];
      const tgt = rutaEnlace.split('?')[0];

      if (cur === tgt || rutaActual.startsWith(tgt)) {
        activo = true;
        enlace.classList.add('bg-red-800', 'font-semibold', 'shadow-md');
        enlace.classList.remove('hover:bg-red-600');
      }
    });

    if (activo) {
      submenuListado.classList.remove('hidden');
      flechaListado.classList.add('rotate-180');
      const padre = document.getElementById('submenu-solicitudes');
      const flechaPadre = document.getElementById('submenu-solicitudes-arrow');
      if (padre && padre.classList.contains('hidden')) padre.classList.remove('hidden');
      if (flechaPadre) flechaPadre.classList.add('rotate-180');
    }

    btnListadoToggle.addEventListener('click', (e) => {
      e.preventDefault();
      const oculto = submenuListado.classList.contains('hidden');
      if (oculto) {
        submenuListado.classList.remove('hidden');
        flechaListado.classList.add('rotate-180');
      } else {
        submenuListado.classList.add('hidden');
        flechaListado.classList.remove('rotate-180');
      }
    });
  }

  const dropdownBotones = document.querySelectorAll('[data-dropdown-toggle]');

  const cerrarPopovers = (idExcepcion = null) => {
    dropdownBotones.forEach(btn => {
      const idDestino = btn.getAttribute('data-dropdown-toggle');
      if (!idDestino) return;
      if (idExcepcion && idExcepcion === idDestino) return;
      const dropdown = document.getElementById(idDestino);
      if (!dropdown) return;
      dropdown.classList.add('hidden');
      const flecha = btn.querySelector('.sidebar-dropdown-arrow');
      if (flecha) flecha.classList.remove('rotate-180');
    });
  };

  dropdownBotones.forEach(btn => {
    const idDestino = btn.getAttribute('data-dropdown-toggle');
    if (!idDestino) return;
    const dropdown = document.getElementById(idDestino);
    if (!dropdown) return;
    const flecha = btn.querySelector('.sidebar-dropdown-arrow');
    let ocultarTimeout = null;

    const mostrar = () => {
      cerrarPopovers(idDestino);
      dropdown.classList.remove('hidden');
      if (flecha) flecha.classList.add('rotate-180');
    };

    const ocultar = () => {
      dropdown.classList.add('hidden');
      if (flecha) flecha.classList.remove('rotate-180');
    };

    const progOcultar = () => {
      ocultarTimeout = window.setTimeout(ocultar, 150);
    };

    const cancelarOcultar = () => {
      if (ocultarTimeout) {
        clearTimeout(ocultarTimeout);
        ocultarTimeout = null;
      }
    };

    btn.addEventListener('mouseenter', () => {
      cancelarOcultar();
      mostrar();
    });

    btn.addEventListener('mouseleave', progOcultar);
    btn.addEventListener('focus', () => {
      cancelarOcultar();
      mostrar();
    });
    btn.addEventListener('blur', progOcultar);

    dropdown.addEventListener('mouseenter', cancelarOcultar);
    dropdown.addEventListener('mouseleave', progOcultar);
  });
})();
