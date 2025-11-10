(function () {
    const btn   = document.getElementById('user-menu-toggle');
    const menu  = document.getElementById('user-menu-dropdown');
    const wrap  = document.getElementById('user-menu-container');
  
    if (!btn || !menu || !wrap) return;
  
    function openMenu() {
      menu.classList.remove('hidden');
      btn.setAttribute('aria-expanded', 'true');
    }
  
    function closeMenu() {
      menu.classList.add('hidden');
      btn.setAttribute('aria-expanded', 'false');
    }
  
    function toggleMenu(e) {
      e.preventDefault();
      const isOpen = !menu.classList.contains('hidden');
      if (isOpen) { closeMenu(); } else { openMenu(); }
    }
  
    btn.addEventListener('click', toggleMenu);
  
    document.addEventListener('click', function (e) {
      if (!menu.classList.contains('hidden')) {
        if (!wrap.contains(e.target)) closeMenu();
      }
    });
  
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') closeMenu();
    });
  })();
  