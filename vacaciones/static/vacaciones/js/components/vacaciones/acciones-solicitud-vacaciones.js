// Script para manejar acciones de la tabla de solicitudes de vacaciones
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('modal-eliminar-solicitud');
    const formEliminar = document.getElementById('form-eliminar-solicitud');
    const codigoSolicitudSpan = document.getElementById('codigo-solicitud-eliminar');
    const btnCancelar = document.getElementById('cancelar-eliminar');
    const deleteLinks = document.querySelectorAll('a[href*="eliminar"]');
    
    // Función para mostrar el modal
    function mostrarModal(codigoSabs, deleteUrl) {
        codigoSolicitudSpan.textContent = codigoSabs;
        formEliminar.action = deleteUrl;
        modal.classList.remove('hidden');
    }
    
    // Función para ocultar el modal
    function ocultarModal() {
        modal.classList.add('hidden');
        formEliminar.action = '';
        codigoSolicitudSpan.textContent = '';
    }
    
    // Event listeners para los enlaces de eliminar
    deleteLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const codigoSabs = this.closest('tr').querySelector('td:first-child').textContent.trim();
            const deleteUrl = this.href;
            mostrarModal(codigoSabs, deleteUrl);
        });
    });
    
    // Event listener para cancelar
    if (btnCancelar) {
        btnCancelar.addEventListener('click', ocultarModal);
    }
    
    // Cerrar modal al hacer clic fuera de él
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                ocultarModal();
            }
        });
    }

    // Animaciones de hover para los iconos de acciones
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
