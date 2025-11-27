$(document).ready(function() {
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  function manejarEliminacion(e) {
    e.preventDefault();
    e.stopPropagation();
    
    const link = $(e.target).closest('a[href*="eliminar"]');

    if (!link.length) return;

    const href = link.attr('href');
    if (!href || !href.includes('periodo')) return;
    
    const row = link.closest('tr');
    const funcionario = row.find('td:first-child').text().trim();
    const fechaInicio = row.find('td:nth-child(2)').text().trim();
    const fechaFin = row.find('td:nth-child(3)').text().trim();
    
    let mensaje = 'Está a punto de eliminar el periodo vacacional';
    if (fechaInicio && fechaFin) {
      mensaje += ` de <strong>${fechaInicio}</strong> a <strong>${fechaFin}</strong>`;
    }
    if (funcionario) {
      mensaje += ` del funcionario <strong>${funcionario}</strong>`;
    }
    mensaje += '. Esta acción no se podrá revertir.';
    
    Swal.fire({
      title: '¿Está seguro?',
      html: mensaje,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#d33',
      cancelButtonColor: '#3085d6',
      confirmButtonText: 'Sí, eliminar',
      cancelButtonText: 'Cancelar'
    }).then((result) => {
      if (result.isConfirmed) {
        const form = $('<form>', {
          method: 'POST',
          action: href,
          css: { display: 'none' }
        });
        
        let csrfToken = getCookie('csrftoken');
        if (!csrfToken) {
          const csrfInputs = $('input[name=csrfmiddlewaretoken]');
          if (csrfInputs.length > 0) {
            csrfToken = csrfInputs.first().val();
          }
        }
        
        if (csrfToken) {
          form.append($('<input>', {
            type: 'hidden',
            name: 'csrfmiddlewaretoken',
            value: csrfToken
          }));
        }
        
        $('body').append(form);
        form.submit();
      }
    });
  }

  $(document).on('click', '#tabla-periodos-vacacionales a[href*="eliminar"], #tabla-periodos-vacacionales a[href*="periodo_vacacional_delete"], #tabla-periodos-vacacionales a[href*="eliminar"] svg, #tabla-periodos-vacacionales a[href*="eliminar"] *', function(e) {
    const link = $(this).closest('a[href*="eliminar"]');
    if (link.length) {
      manejarEliminacion(e);
    }
  });
});
