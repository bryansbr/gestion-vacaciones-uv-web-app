document.addEventListener('DOMContentLoaded', function() {
  const formulario = document.querySelector('form[method="POST"]');
  const btnEnviar = formulario ? formulario.querySelector('button[type="submit"]') : null;
  
  if (!formulario || !btnEnviar) {
    return;
  }
  
  const esModoEdicion = btnEnviar.textContent.trim().toLowerCase().includes('actualizar');
  
  if (!esModoEdicion) {
    return;
  }
  
  let formularioCambiado = false;
  
  const inputs = formulario.querySelectorAll('input, select, textarea');
  inputs.forEach(function(input) {
    input.addEventListener('change', function() {
      formularioCambiado = true;
    });
    
    input.addEventListener('input', function() {
      formularioCambiado = true;
    });
  });
  
  formulario.addEventListener('submit', function(e) {
    if (!formularioCambiado) {
      return;
    }
    
    e.preventDefault();
    
    Swal.fire({
      title: '¿Confirmar actualización?',
      html: 'Está a punto de actualizar el periodo vacacional. Esta acción no se podrá revertir.',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#3085d6',
      cancelButtonColor: '#d33',
      confirmButtonText: 'Sí, actualizar',
      cancelButtonText: 'Cancelar'
    }).then((resultado) => {
      if (resultado.isConfirmed) {
        formularioCambiado = false;
        formulario.submit();
      }
    });
  });
});
