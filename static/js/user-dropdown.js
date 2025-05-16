const userMenuToggle = document.getElementById('user-menu-toggle');
const userMenuDropdown = document.getElementById('user-menu-dropdown');
const userMenuContainer = document.getElementById('user-menu-container');

if (userMenuToggle && userMenuDropdown) {
  userMenuToggle.addEventListener('click', function(e) {
    e.stopPropagation();

    const rect = userMenuToggle.getBoundingClientRect();
    const navbar = document.querySelector('header');
    const navbarRect = navbar.getBoundingClientRect();

    userMenuDropdown.style.top = `${navbarRect.bottom}px`;
    userMenuDropdown.style.right = `${window.innerWidth - rect.right}px`;
    userMenuDropdown.classList.toggle('hidden');
  });
  
  document.addEventListener('click', function(e) {
    if (!userMenuContainer.contains(e.target)) {
      userMenuDropdown.classList.add('hidden');
    }
  });
}
