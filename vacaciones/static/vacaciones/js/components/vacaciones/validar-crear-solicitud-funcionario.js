document.addEventListener('DOMContentLoaded', function () {
  const btnCrear = document.getElementById('btn-crear-solicitud-funcionario');
  
  if (!btnCrear) {
    return;
  }
  
  if (typeof validarCrearSolicitud === 'undefined') {
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
      const tienePeriodos = btnCrear.dataset.tienePeriodos === 'true';
      const tienePeriodosDisponibles = btnCrear.dataset.tienePeriodosDisponibles === 'true';
      const tieneSolicitudActiva = btnCrear.dataset.tieneSolicitudActiva === 'true';
      const solicitudActivaCodigo = btnCrear.dataset.solicitudActivaCodigo || '';
      const tieneReintegroEnCurso = btnCrear.dataset.tieneReintegroEnCurso === 'true';
      const resultado = validarCrearSolicitud({
        tiene_periodos: tienePeriodos,
        tiene_periodos_disponibles: tienePeriodosDisponibles,
        tiene_solicitud_activa: tieneSolicitudActiva,
        solicitud_activa_codigo: solicitudActivaCodigo,
        tiene_reintegro_en_curso: tieneReintegroEnCurso
      });
      
      if (!resultado.puede_crear) {
        mostrarAlertaValidacion(resultado);
        return;
      }
      
    } catch (error) {
      const urlCrear = btnCrear.dataset.urlCrear;
      if (urlCrear) {
        window.location.href = urlCrear;
      }
    }
  });
});
