// Script para manejar la animación de carga del formulario de solicitud de vacaciones
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    const submitBtn = document.getElementById('submit-btn');
    const loadingSpinner = document.getElementById('loading-spinner');
    
    if (form && submitBtn && loadingSpinner) {
        form.addEventListener('submit', function(e) {
            submitBtn.style.display = 'none';
            loadingSpinner.classList.remove('hidden');
        });
    }
});
