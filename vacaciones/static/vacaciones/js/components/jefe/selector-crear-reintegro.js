document.addEventListener('DOMContentLoaded', function () {
  const btnCrear = document.getElementById('btn-crear-reintegro-jefe');
  
  if (!btnCrear) return;
  
  if (btnCrear) {
    btnCrear.addEventListener('click', function() {
      Swal.fire({
        title: '¿Para quién desea crear el reintegro?',
        html: `
          <div class="flex flex-col gap-3 mt-4">
            <button 
              id="swal-btn-para-mi" 
              class="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors duration-200 text-left"
            >
              <strong>Para mí</strong>
              <p class="text-sm mt-1 opacity-90">Cree un reintegro de vacaciones para usted.</p>
            </button>
            <button 
              id="swal-btn-para-otro" 
              class="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors duration-200 text-left"
            >
              <strong>Para otro funcionario</strong>
              <p class="text-sm mt-1 opacity-90">Cree un reintegro de vacaciones para un funcionario bajo su mando.</p>
            </button>
          </div>
        `,
        showCancelButton: false,
        showConfirmButton: false,
        allowOutsideClick: true,
        didOpen: () => {
          const btnParaMi = document.getElementById('swal-btn-para-mi');
          const btnParaOtro = document.getElementById('swal-btn-para-otro');
          const funcionariosData = JSON.parse(btnCrear.dataset.funcionarios || '[]');
          const jefeId = btnCrear.dataset.jefeId;
          
          if (btnParaMi) {
            btnParaMi.addEventListener('click', function() {
              Swal.close();
              const jefeData = funcionariosData.find(f => f.id.toString() === jefeId);
              
              if (typeof validarCrearReintegro !== 'undefined' && typeof mostrarAlertaValidacion !== 'undefined') {
                const resultado = validarCrearReintegro({
                  tiene_solicitudes_autorizadas: jefeData?.tiene_solicitudes_autorizadas || false
                });
                
                if (!resultado.puede_crear) {
                  mostrarAlertaValidacion(resultado);
                  return;
                }
              } else if (!jefeData || !jefeData.tiene_solicitudes_autorizadas) {
                Swal.fire({
                  icon: 'error',
                  title: '¡Atención!',
                  text: 'No tiene solicitudes autorizadas disponibles para reintegro.',
                  confirmButtonText: 'OK'
                });
                return;
              }
              
              if (jefeData.solicitudes_autorizadas.length > 1) {
                let solicitudesOptionsHtml = '<option value="">Seleccione la solicitud</option>';
                jefeData.solicitudes_autorizadas.forEach(sol => {
                  solicitudesOptionsHtml += `<option value="${sol.id}">${sol.codigo_sabs} - ${sol.fecha_inicio} al ${sol.fecha_fin}</option>`;
                });
                
                Swal.fire({
                  title: 'Seleccione la solicitud autorizada',
                  html: `<select id="swal-select-solicitud-jefe" class="swal2-input">${solicitudesOptionsHtml}</select>`,
                  showCancelButton: true,
                  confirmButtonText: 'Continuar',
                  cancelButtonText: 'Cancelar',
                  preConfirm: () => {
                    const selectSolicitud = document.getElementById('swal-select-solicitud-jefe');
                    if (!selectSolicitud || !selectSolicitud.value) {
                      Swal.showValidationMessage('Debe seleccionar una solicitud');
                      return false;
                    }
                    return selectSolicitud.value;
                  }
                }).then((resultSolicitud) => {
                  if (resultSolicitud.isConfirmed && resultSolicitud.value) {
                    window.location.href = btnCrear.dataset.urlCrear + 
                      '?funcionario_id=' + jefeId + 
                      '&solicitud_id=' + resultSolicitud.value;
                  }
                });
              } else {
                const solicitud = jefeData.solicitudes_autorizadas[0];
                window.location.href = btnCrear.dataset.urlCrear + 
                  '?funcionario_id=' + jefeId + 
                  '&solicitud_id=' + solicitud.id;
              }
            });
          }
          
          if (btnParaOtro) {
            btnParaOtro.addEventListener('click', function() {
              Swal.close();
              
              const funcionariosConSolicitudes = funcionariosData.filter(func => 
                func.tiene_solicitudes_autorizadas && func.id.toString() !== jefeId
              );
              
              if (!funcionariosConSolicitudes || funcionariosConSolicitudes.length === 0) {
                Swal.fire({
                  icon: 'error',
                  title: 'No hay funcionarios disponibles',
                  text: 'No hay funcionarios bajo su mando con solicitudes autorizadas disponibles para reintegro.'
                });
                return;
              }
              
              let optionsHtml = '<option value="">Seleccione un funcionario</option>';
              funcionariosConSolicitudes.forEach(func => {
                optionsHtml += `<option value="${func.id}">${func.nombre} ${func.apellido} - ${func.facultad_dependencia}</option>`;
              });
              
              Swal.fire({
                title: 'Seleccione el funcionario',
                html: `<select id="swal-select-funcionario" class="swal2-input">${optionsHtml}</select>`,
                showCancelButton: true,
                confirmButtonText: 'Continuar',
                cancelButtonText: 'Cancelar',
                preConfirm: () => {
                  const select = document.getElementById('swal-select-funcionario');
                  if (!select || !select.value) {
                    Swal.showValidationMessage('Debe seleccionar un funcionario');
                    return false;
                  }
                  return select.value;
                }
              }).then((result) => {
                if (result.isConfirmed && result.value) {
                  const funcionarioSeleccionado = funcionariosConSolicitudes.find(f => f.id.toString() === result.value);
                  
                  if (typeof validarCrearReintegro !== 'undefined' && typeof mostrarAlertaValidacion !== 'undefined') {
                    const resultado = validarCrearReintegro({
                      tiene_solicitudes_autorizadas: funcionarioSeleccionado?.tiene_solicitudes_autorizadas || false,
                      nombre_funcionario: funcionarioSeleccionado ? `${funcionarioSeleccionado.nombre} ${funcionarioSeleccionado.apellido}` : ''
                    });
                    
                    if (!resultado.puede_crear) {
                      mostrarAlertaValidacion(resultado);
                      return;
                    }
                  } else if (!funcionarioSeleccionado || !funcionarioSeleccionado.tiene_solicitudes_autorizadas) {
                    Swal.fire({
                      icon: 'error',
                      title: '¡Atención!',
                      html: `El funcionario <strong>${funcionarioSeleccionado.nombre} ${funcionarioSeleccionado.apellido}</strong> no tiene solicitudes autorizadas disponibles para reintegro.`,
                      confirmButtonText: 'OK'
                    });
                    return;
                  }
                  
                  if (funcionarioSeleccionado.solicitudes_autorizadas.length > 1) {
                    let solicitudesOptionsHtml = '<option value="">Seleccione la solicitud</option>';
                    funcionarioSeleccionado.solicitudes_autorizadas.forEach(sol => {
                      solicitudesOptionsHtml += `<option value="${sol.id}">${sol.codigo_sabs} - ${sol.fecha_inicio} al ${sol.fecha_fin}</option>`;
                    });
                    
                    Swal.fire({
                      title: 'Seleccione la solicitud autorizada',
                      html: `<select id="swal-select-solicitud" class="swal2-input">${solicitudesOptionsHtml}</select>`,
                      showCancelButton: true,
                      confirmButtonText: 'Continuar',
                      cancelButtonText: 'Cancelar',
                      preConfirm: () => {
                        const selectSolicitud = document.getElementById('swal-select-solicitud');
                        if (!selectSolicitud || !selectSolicitud.value) {
                          Swal.showValidationMessage('Debe seleccionar una solicitud');
                          return false;
                        }
                        return {
                          funcionario_id: result.value,
                          solicitud_id: selectSolicitud.value
                        };
                      }
                    }).then((resultSolicitud) => {
                      if (resultSolicitud.isConfirmed && resultSolicitud.value) {
                        window.location.href = btnCrear.dataset.urlCrear + 
                          '?funcionario_id=' + resultSolicitud.value.funcionario_id + 
                          '&solicitud_id=' + resultSolicitud.value.solicitud_id;
                      }
                    });
                  } else {
                    const solicitud = funcionarioSeleccionado.solicitudes_autorizadas[0];
                    window.location.href = btnCrear.dataset.urlCrear + 
                      '?funcionario_id=' + result.value + 
                      '&solicitud_id=' + solicitud.id;
                  }
                }
              });
            });
          }
        }
      });
    });
  }
});
