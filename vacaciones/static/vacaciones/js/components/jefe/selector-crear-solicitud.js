document.addEventListener('DOMContentLoaded', function () {
  const btnCrear = document.getElementById('btn-crear-solicitud-jefe');
  
  if (btnCrear) {
    btnCrear.addEventListener('click', function() {
      Swal.fire({
        title: '¿Para quién desea crear la solicitud?',
        html: `
          <div class="flex flex-col gap-3 mt-4">
            <button 
              id="swal-btn-para-mi" 
              class="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors duration-200 text-left"
            >
              <strong>Para mí</strong>
              <p class="text-sm mt-1 opacity-90">Cree una solicitud de vacaciones para usted.</p>
            </button>
            <button 
              id="swal-btn-para-otro" 
              class="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors duration-200 text-left"
            >
              <strong>Para otro funcionario</strong>
              <p class="text-sm mt-1 opacity-90">Cree una solicitud de vacaciones para un funcionario bajo su mando.</p>
            </button>
          </div>
        `,
        showCancelButton: false,
        showConfirmButton: false,
        allowOutsideClick: true,
        didOpen: () => {
          const btnParaMi = document.getElementById('swal-btn-para-mi');
          const btnParaOtro = document.getElementById('swal-btn-para-otro');
          const jefeId = btnCrear.dataset.jefeId;
          
          if (btnParaMi) {
            btnParaMi.addEventListener('click', function() {
              const tienePeriodos = btnCrear.dataset.tienePeriodos === 'true';
              const tieneSolicitudActiva = btnCrear.dataset.tieneSolicitudActiva === 'true';
              
              if (!tienePeriodos) {
                Swal.close();
                Swal.fire({
                  icon: 'error',
                  title: '¡Atención!',
                  text: 'No puede solicitar vacaciones porque no tiene periodos registrados en el sistema. Contacte al administrador para que registre su(s) periodo(s) vacacional(es).',
                  confirmButtonText: 'OK'
                });
                return;
              }
              
              if (tieneSolicitudActiva) {
                const codigo = btnCrear.dataset.solicitudActivaCodigo || '';
                Swal.close();
                Swal.fire({
                  icon: 'warning',
                  title: 'Solicitud en curso',
                  html: `Ya tiene una solicitud de vacaciones en curso${codigo ? ` (${codigo})` : ''}. Debe culminar el disfrute del periodo actual antes de crear una nueva solicitud.`,
                  confirmButtonText: 'OK'
                });
                return;
              }
              
              Swal.close();
              window.location.href = btnCrear.dataset.urlCrear + '?funcionario_id=' + jefeId;
            });
          }
          
          if (btnParaOtro) {
            btnParaOtro.addEventListener('click', function() {
              Swal.close();
              const funcionariosData = JSON.parse(btnCrear.dataset.funcionarios || '[]');
              
              if (!funcionariosData || funcionariosData.length === 0) {
                Swal.fire({
                  icon: 'error',
                  title: 'No hay funcionarios disponibles',
                  text: 'No hay funcionarios bajo su mando. Contacte al administrador.'
                });
                return;
              }
              
              let optionsHtml = '<option value="">Seleccione un funcionario</option>';
              funcionariosData.forEach(func => {
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
                  const funcionarioSeleccionado = funcionariosData.find(f => f.id.toString() === result.value);
                  
                  if (!funcionarioSeleccionado.tiene_periodos) {
                    Swal.fire({
                      icon: 'error',
                      title: '¡Atención!',
                      html: `El(la) funcionario(a) <strong>${funcionarioSeleccionado.nombre} ${funcionarioSeleccionado.apellido}</strong> no tiene periodos vacacionales registrados. Contacte al administrador para que registre su(s) periodo(s) vacacional(es).`,
                      confirmButtonText: 'OK'
                    });
                    return;
                  }
                  
                  if (funcionarioSeleccionado && funcionarioSeleccionado.tiene_solicitud_activa) {
                    Swal.fire({
                      icon: 'info',
                      title: 'Solicitud en curso',
                      html: `El(la) funcionario(a) <strong>${funcionarioSeleccionado.nombre} ${funcionarioSeleccionado.apellido}</strong> ya tiene una solicitud de vacaciones en curso${funcionarioSeleccionado.solicitud_activa_codigo ? ` (${funcionarioSeleccionado.solicitud_activa_codigo})` : ''}.  Puede visualizarla en la opción "Listado de solicitudes".`,
                      confirmButtonText: 'OK'
                    });
                    return;
                  }
                  
                  window.location.href = btnCrear.dataset.urlCrear + '?funcionario_id=' + result.value;
                }
              });
            });
          }
        }
      });
    });
  }
});
