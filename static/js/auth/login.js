document.addEventListener("DOMContentLoaded", function() {
  const form = document.querySelector('form');
  const submitButton = form.querySelector('button[type="submit"]');
  const emailInput = form.querySelector('input[name="username"]');
  const errorBox = document.querySelector('.bg-red-100'); // Captura el div de error si existe

  // Mostrar spinner cuando envíen el formulario
  form.addEventListener("submit", function() {
    submitButton.disabled = true;
    submitButton.innerHTML = `
      <div class="flex items-center justify-center gap-2">
        <svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
        </svg>
        <span>Iniciando sesión...</span>
      </div>
    `;
  });

  // Eliminar el div de error al hacer focus en el campo de email
  if (emailInput && errorBox) {
    emailInput.addEventListener("focus", function() { errorBox.remove(); });
  }
}); 