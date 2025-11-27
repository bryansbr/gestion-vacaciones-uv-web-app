document.addEventListener('DOMContentLoaded', function () {
  const btnCrear = document.getElementById('btn-crear-reintegro-funcionario');
  
  if (!btnCrear) return;
  
  if (typeof validarCrearReintegro === 'undefined') {
    btnCrear.addEventListener('click', function(e) {
      const urlCrear = btnCrear.dataset.urlCrear;
      if (urlCrear) {
        window.location.href = urlCrear;
      }
    });
    return;
  }
  
  if (typeof mostrarAlertaValidacion === 'undefined') {
    btnCrear.addEventListener('click', function(e) {
      const urlCrear = btnCrear.dataset.urlCrear;
      if (urlCrear) {
        window.location.href = urlCrear;
      }
    });
    return;
  }
  
  btnCrear.addEventListener('click', function(e) {
    e.preventDefault();
    e.stopPropagation();
    
    try {
      const tieneSolicitudesAutorizadas = btnCrear.dataset.tieneSolicitudesAutorizadas === 'true';
      const resultado = validarCrearReintegro({
        tiene_solicitudes_autorizadas: tieneSolicitudesAutorizadas
      });
      
      if (!resultado.puede_crear) {
        mostrarAlertaValidacion(resultado);
        return;
      }
      
      const urlCrear = btnCrear.dataset.urlCrear;
      const solicitudId = btnCrear.dataset.solicitudId;
      if (urlCrear) {
        const url = solicitudId ? `${urlCrear}?solicitud_id=${solicitudId}` : urlCrear;
        window.location.href = url;
      }
    } catch (error) {
      console.error('Error en validación de reintegro:', error);
      const urlCrear = btnCrear.dataset.urlCrear;
      if (urlCrear) {
        window.location.href = urlCrear;
      }
    }
  });
});
