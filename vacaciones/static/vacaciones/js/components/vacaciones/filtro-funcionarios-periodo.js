document.addEventListener('DOMContentLoaded', function() {
  const filtroFacultad = document.getElementById('id_facultad_dependencia_filtro');
  const selectFuncionario = document.getElementById('id_funcionario');
  
  if (!filtroFacultad || !selectFuncionario) return;

  const contenedorDatos = document.getElementById('datos-funcionarios-periodo');
  if (!contenedorDatos) return;

  let datosFuncionarios = [];

  try {
    const datosJson = contenedorDatos.dataset.funcionarios;
    if (datosJson) {
      datosFuncionarios = JSON.parse(datosJson);
    }
  } catch (e) { return; }

  const facultadInicial = contenedorDatos.dataset.facultadInicial;

  if (facultadInicial) {
    filtroFacultad.value = facultadInicial;
  }

  function filtrarFuncionarios() {
    const facultadId = filtroFacultad.value ? parseInt(filtroFacultad.value) : null;
    const funcionarioSeleccionado = selectFuncionario.value;
    
    while (selectFuncionario.options.length > 0) {
      selectFuncionario.remove(0);
    }
    
    const opcionPorDefecto = document.createElement('option');
    opcionPorDefecto.value = '';
    opcionPorDefecto.textContent = '---------';
    selectFuncionario.appendChild(opcionPorDefecto);
    
    let funcionariosFiltrados = datosFuncionarios;

    if (facultadId) {
      funcionariosFiltrados = datosFuncionarios.filter(function(func) {
        return func.facultad_dependencia_id === facultadId;
      });
    }
    
    funcionariosFiltrados.forEach(function(func) {
      const opcion = document.createElement('option');
      opcion.value = func.id;
      opcion.textContent = func.nombre_completo;

      if (func.id.toString() === funcionarioSeleccionado) {
        opcion.selected = true;
      }

      selectFuncionario.appendChild(opcion);
    });
    
    if (funcionarioSeleccionado && !selectFuncionario.value) {
      const funcionarioOriginal = datosFuncionarios.find(function(func) {
        return func.id.toString() === funcionarioSeleccionado;
      });

      if (funcionarioOriginal) {
        const opcion = document.createElement('option');
        opcion.value = funcionarioOriginal.id;
        opcion.textContent = funcionarioOriginal.nombre_completo;
        opcion.selected = true;
        selectFuncionario.insertBefore(opcion, selectFuncionario.options[1]);
      }
    }
  }

  if (filtroFacultad.value) {
    filtrarFuncionarios();
  }

  filtroFacultad.addEventListener('change', function() {
    filtrarFuncionarios();
  });

  const formulario = document.getElementById('periodo-vacacional-form');
  
  if (formulario) {
    formulario.addEventListener('submit', function() {
      filtroFacultad.disabled = true;
    });
  }
});
