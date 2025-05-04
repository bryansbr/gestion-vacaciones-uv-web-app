
document.addEventListener("DOMContentLoaded", function () {
  const menuToggle = document.getElementById("menu-toggle");
  const sidebar = document.getElementById("sidebar");
  const closeSidebarBtn = document.getElementById("close-sidebar");

  // Mostrar el sidebar al hacer clic en el ícono hamburguesa
  menuToggle?.addEventListener("click", function () {
    sidebar.classList.remove("hidden");
    sidebar.classList.add("block");
  });

  // Ocultar el sidebar al hacer clic en el ícono de cierre
  closeSidebarBtn?.addEventListener("click", function () {
    sidebar.classList.remove("block");
    sidebar.classList.add("hidden");
  });
});
