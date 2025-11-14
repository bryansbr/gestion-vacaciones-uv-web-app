document.addEventListener('DOMContentLoaded', function() {
  const contenedor = document.getElementById('variables-container');
  if (!contenedor) return;

  const funcionariosData = contenedor.dataset.funcionariosBajoCoord;
  if (!funcionariosData) return;

  let funcionarios = [];
  try {
    funcionarios = JSON.parse(funcionariosData);
  } catch (e) {
    console.error('Error parsing funcionarios data:', e);
    return;
  }

  const selector = document.getElementById('funcionario-selector');
  if (!selector) return;

  funcionarios.forEach(func => {
    const opcion = document.createElement('option');
    opcion.value = func.id;
    opcion.textContent = `${func.nombre} ${func.apellido} - ${func.facultad_dependencia || 'Sin dependencia'}`;
    if (func.tiene_solicitudes_autorizadas) {
      opcion.textContent += ' ✓';
    }
    selector.appendChild(opcion);
  });

  selector.addEventListener('change', function() {
    const funcionarioId = this.value;
    if (!funcionarioId) {
      const idNumero = document.querySelector('input[name="numero_identificacion"]');
      const nombreFunc = document.querySelector('input[name="nombre_funcionario"]');
      const estamento = document.querySelector('select[name="estamento"]');
      const facultad = document.querySelector('select[name="facultad_dependencia"]');
      const sede = document.querySelector('select[name="sede"]');
      
      if (idNumero) idNumero.value = '';
      if (nombreFunc) nombreFunc.value = '';
      if (estamento) estamento.value = '';
      if (facultad) facultad.value = '';
      if (sede) sede.value = '';
      
      const solicitudSelect = document.querySelector('select[name="solicitud_vacaciones"]');
      if (solicitudSelect) {
        solicitudSelect.innerHTML = '<option value="">-- Seleccione una solicitud --</option>';
      }
      return;
    }

    const funcionario = funcionarios.find(f => f.id.toString() === funcionarioId.toString());
    
    if (!funcionario) return;
    
    const solicitudSelect = document.querySelector('select[name="solicitud_vacaciones"]');
    
    if (solicitudSelect && funcionario.solicitudes_autorizadas) {
      solicitudSelect.innerHTML = '<option value="">-- Seleccione una solicitud --</option>';
      funcionario.solicitudes_autorizadas.forEach(sol => {
        const opcion = document.createElement('option');
        opcion.value = sol.id;
        opcion.textContent = `${sol.codigo_sabs} - ${sol.fecha_inicio} a ${sol.fecha_fin}`;
        solicitudSelect.appendChild(opcion);
      });
    }

    const formulario = document.getElementById('form-reintegro-vacaciones');
    if (formulario) {
      const url = new URL(window.location.href);
      url.searchParams.set('funcionario_id', funcionarioId);
      window.history.replaceState({}, '', url);
    }
  });

  const parametrosUrl = new URLSearchParams(window.location.search);
  const funcionarioIdFromUrl = parametrosUrl.get('funcionario_id');
  if (funcionarioIdFromUrl) {
    selector.value = funcionarioIdFromUrl;
    selector.dispatchEvent(new Event('change'));
  }
});

