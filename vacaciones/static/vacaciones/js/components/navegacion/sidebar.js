document.addEventListener("DOMContentLoaded", function () {
  const menuToggle = document.querySelector("[data-toggle='sidebar']");
  const sidebar = document.getElementById("sidebar");
  const closeSidebarBtn = document.querySelector("[data-action='close-sidebar']");

  if (!menuToggle || !sidebar) return;

  const abrirSidebar = () => {
    sidebar.classList.remove("hidden");
    sidebar.classList.add("block");
  };

  const cerrarSidebar = () => {
    sidebar.classList.remove("block");
    sidebar.classList.add("hidden");
  };

  menuToggle.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();

    const estaAbierto = sidebar.classList.contains("block");
    if (estaAbierto) {
      cerrarSidebar();
    } else {
      abrirSidebar();
    }
  });

  if (closeSidebarBtn) {
    closeSidebarBtn.addEventListener("click", (event) => {
      event.preventDefault();
      cerrarSidebar();
    });
  }

  document.addEventListener("click", (event) => {
    if (!sidebar.contains(event.target) && event.target !== menuToggle) {
      cerrarSidebar();
    }
  });
}); 