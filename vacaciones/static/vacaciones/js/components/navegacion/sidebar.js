document.addEventListener("DOMContentLoaded", function () {
  const menuAlternar = document.querySelector("[data-toggle='sidebar']");
  const sidebar = document.getElementById("sidebar");
  const btnCerrarSidebar = document.querySelector("[data-action='close-sidebar']");

  if (!menuAlternar || !sidebar) return;

  const abrirSidebar = () => {
    sidebar.classList.remove("hidden");
    sidebar.classList.add("block");
  };

  const cerrarSidebar = () => {
    sidebar.classList.remove("block");
    sidebar.classList.add("hidden");
  };

  menuAlternar.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();

    const estaAbierto = sidebar.classList.contains("block");
    if (estaAbierto) {
      cerrarSidebar();
    } else {
      abrirSidebar();
    }
  });

  if (btnCerrarSidebar) {
    btnCerrarSidebar.addEventListener("click", (event) => {
      event.preventDefault();
      cerrarSidebar();
    });
  }

  document.addEventListener("click", (event) => {
    if (!sidebar.contains(event.target) && event.target !== menuAlternar) {
      cerrarSidebar();
    }
  });

  const enlaceEstadoVacaciones = document.getElementById('sidebar-link-estado-vacaciones');

  if (enlaceEstadoVacaciones) {
    const rutaActual = window.location.pathname;
    const rutaEnlace = enlaceEstadoVacaciones.getAttribute('data-url-path') || '';
    const rutaActualLimpia = rutaActual.split('?')[0];
    const rutaEnlaceLimpia = rutaEnlace.split('?')[0];
    
    if (rutaActualLimpia === rutaEnlaceLimpia || rutaActual.startsWith(rutaEnlaceLimpia)) {
      enlaceEstadoVacaciones.classList.add('bg-red-800', 'font-semibold', 'shadow-md');
      enlaceEstadoVacaciones.classList.remove('hover:bg-red-600');
      const icono = enlaceEstadoVacaciones.querySelector('svg');
      const texto = enlaceEstadoVacaciones.querySelector('.sidebar-text');
      if (icono) icono.classList.add('text-white');
      if (texto) texto.classList.add('text-white');
    }
  }

  const enlaceReportes = document.getElementById('sidebar-link-reportes');

  if (enlaceReportes) {
    const rutaActual = window.location.pathname;
    const rutaEnlace = enlaceReportes.getAttribute('data-url-path') || '';
    const rutaActualLimpia = rutaActual.split('?')[0];
    const rutaEnlaceLimpia = rutaEnlace.split('?')[0];
    
    if (rutaActualLimpia === rutaEnlaceLimpia || rutaActual.startsWith(rutaEnlaceLimpia)) {
      enlaceReportes.classList.add('bg-red-800', 'font-semibold', 'shadow-md');
      enlaceReportes.classList.remove('hover:bg-red-600');
      const icono = enlaceReportes.querySelector('svg');
      const texto = enlaceReportes.querySelector('.sidebar-text');
      if (icono) icono.classList.add('text-white');
      if (texto) texto.classList.add('text-white');
    }
  }

  function resaltarEnlaceActivo(enlace) {
    enlace.classList.add('bg-red-800', 'font-semibold', 'shadow-md');
    enlace.classList.remove('hover:bg-red-600');
    const iconos = enlace.querySelectorAll('svg');
    const texto = enlace.querySelector('.sidebar-text');
    iconos.forEach(icono => icono.classList.add('text-white'));
    if (texto) texto.classList.add('text-white');
  }

  function verificarRutaActiva(enlace) {
    const rutaActual = window.location.pathname;
    const rutaEnlace = enlace.getAttribute('data-url-path') || enlace.getAttribute('href') || '';
    if (!rutaEnlace) return false;
    
    const rutaActualLimpia = rutaActual.split('?')[0];
    const rutaEnlaceLimpia = rutaEnlace.split('?')[0];
    
    if (rutaActualLimpia === rutaEnlaceLimpia) {
      return true;
    }
    
    if (rutaEnlaceLimpia && rutaEnlaceLimpia !== '/' && rutaActual.startsWith(rutaEnlaceLimpia)) {
      return true;
    }
    
    return false;
  }

  const todosLosEnlaces = document.querySelectorAll('.sidebar-link[data-url-path], .sidebar-link[href], .popover-link[data-url-path], .popover-link[href]');
  
  todosLosEnlaces.forEach(enlace => {
    if (verificarRutaActiva(enlace)) {
      resaltarEnlaceActivo(enlace);
      
      const submenuPadre = enlace.closest('ul');
      if (submenuPadre && submenuPadre.id) {
        submenuPadre.classList.remove('hidden');
        submenuPadre.classList.add('block');
        
        const botonToggle = document.getElementById(submenuPadre.id + '-toggle');
        if (botonToggle) {
          const flecha = document.getElementById(submenuPadre.id + '-arrow');
          if (flecha) {
            flecha.classList.add('rotate-180');
          }
        }
      }
      
      const popoverPadre = enlace.closest('.sidebar-popover');
      if (popoverPadre) {
        popoverPadre.classList.remove('hidden');
        const botonPadre = document.querySelector(`[data-dropdown-toggle="${popoverPadre.id}"]`);
        if (botonPadre) {
          const flecha = botonPadre.querySelector('.sidebar-dropdown-arrow');
          if (flecha) {
            flecha.classList.add('rotate-180');
          }
        }
      }
    }
  });
});
