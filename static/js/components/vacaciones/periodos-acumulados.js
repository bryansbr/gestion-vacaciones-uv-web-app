// Script para manejar el modal de periodos acumulados
document.addEventListener('DOMContentLoaded', function() {
    // Mostrar el modal al cargar la página
    var modal = document.getElementById('modal-alerta-periodos');
    var btn = document.getElementById('cerrar-modal-periodos');
    
    if (modal && btn) {
        modal.classList.remove('hidden');
        
        btn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            modal.classList.add('hidden');
            // Evitar que el foco pase al siguiente input (como el datepicker)
            setTimeout(function() {
                document.activeElement.blur();
            }, 10);
            return false;
        };
        
        // Prevenir selección de periodo no habilitado
        var selectPeriodo = document.getElementById('id_periodo_vacacional');
        if (selectPeriodo) {
            selectPeriodo.addEventListener('change', function(e) {
                var select = e.target;
                var selected = select.options[select.selectedIndex];
                if (selected.disabled) {
                    // Volver a seleccionar el más antiguo
                    select.value = select.getAttribute('data-periodo-antiguo');
                    modal.classList.remove('hidden');
                }
            });
        }
    }
}); 