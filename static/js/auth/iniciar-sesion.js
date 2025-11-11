document.addEventListener('DOMContentLoaded', function() {
  const formulario = document.querySelector('form[action$="login/"]') || document.querySelector('form');
  if (!formulario) {
    return;
  }

  const btnEnvio = formulario.querySelector('button[type="submit"]');
  const campoCorreo = formulario.querySelector('input[name="username"]');
  const contenedorError = document.querySelector('.bg-red-100');
  let spinnerAplicado = false;

  if (btnEnvio) {
    formulario.addEventListener('submit', function() {
      if (spinnerAplicado) {
        return;
      }
      spinnerAplicado = true;
      btnEnvio.disabled = true;
      btnEnvio.innerHTML = `
        <div class="flex items-center justify-center gap-2">
          <svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
          </svg>
          <span>Iniciando sesión...</span>
        </div>
      `;
    });
  }

  if (campoCorreo && contenedorError) {
    campoCorreo.addEventListener('focus', function() {
      contenedorError.remove();
    }, { once: true });
  }
});
