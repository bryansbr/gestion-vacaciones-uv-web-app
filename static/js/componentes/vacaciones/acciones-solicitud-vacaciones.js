// Script para manejar acciones de la tabla de solicitudes de vacaciones
document.addEventListener('DOMContentLoaded', function() {
    const deleteLinks = document.querySelectorAll('a[href*="eliminar"]');
    
    deleteLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const confirmMessage = '¿Está seguro de que desea eliminar esta solicitud de vacaciones? Esta acción no se puede deshacer.';
            
            if (confirm(confirmMessage)) {
                window.location.href = this.href;
            }
        });
    });

    const actionIcons = document.querySelectorAll('.flex.space-x-2 a');
    
    actionIcons.forEach(function(icon) {
        icon.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.1)';
        });
        
        icon.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });
});
