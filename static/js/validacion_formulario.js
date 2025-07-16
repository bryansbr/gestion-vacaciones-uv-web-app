// Script para deshabilitar formulario cuando no hay periodos vacacionales
document.addEventListener('DOMContentLoaded', function() {
    // Verificar si el formulario debe estar deshabilitado
    const form = document.getElementById('form-disabled');
    if (form) {
        // Deshabilitar todos los campos del formulario
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(function(input) {
            input.disabled = true;
            input.classList.add('bg-gray-100', 'cursor-not-allowed');
        });
        
        // Deshabilitar también los campos que ya están deshabilitados pero con estilos diferentes
        const disabledInputs = form.querySelectorAll('input[disabled], select[disabled], textarea[disabled]');
        disabledInputs.forEach(function(input) {
            input.classList.add('bg-gray-100', 'cursor-not-allowed');
        });
    }
}); 