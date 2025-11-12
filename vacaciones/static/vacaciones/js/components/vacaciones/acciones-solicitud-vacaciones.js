document.addEventListener('DOMContentLoaded', function() {
    const formEliminar = document.getElementById('form-eliminar-solicitud');
    const eliminarLinks = document.querySelectorAll('a[href*="eliminar"]');

    eliminarLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const codigoSabs = this.closest('tr').querySelector('td:first-child').textContent.trim();
            const eliminarUrl = this.href;

            if (!formEliminar) {
                window.location.href = eliminarUrl;
                return;
            }

            Swal.fire({
                title: 'Confirmar eliminación',
                html: `¿Estás seguro de que deseas eliminar la solicitud de vacaciones <strong>${codigoSabs}</strong>?. Esta acción no se puede deshacer.`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#6b7280',
                confirmButtonText: 'Sí, eliminar',
                cancelButtonText: 'Cancelar'
            }).then((resultado) => {
                if (resultado.isConfirmed) {
                    try {
                        localStorage.setItem('solicitud_eliminada', '1');
                        localStorage.setItem('solicitud_eliminada_codigo', codigoSabs);
                    } catch (_) {}
                    formEliminar.action = eliminarUrl;
                    formEliminar.submit();
                }
            });
        });
    });

    const accionesIconos = document.querySelectorAll('.flex.space-x-2 a');
    
    accionesIconos.forEach(function(icono) {
        icono.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.1)';
        });
        
        icono.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });
});
