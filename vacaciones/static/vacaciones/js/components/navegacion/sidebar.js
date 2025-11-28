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
});
