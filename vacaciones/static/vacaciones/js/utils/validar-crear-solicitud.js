/**
 * Validar si se puede crear una solicitud de vacaciones antes de proceder con la creación.
 * 
 * @param {Object} datos
 * @param {boolean} datos.tiene_periodos
 * @param {boolean} datos.tiene_periodos_disponibles
 * @param {boolean} datos.tiene_solicitud_activa
 * @param {string} datos.solicitud_activa_codigo
 * @param {boolean} datos.tiene_reintegro_en_curso
 * @param {string} datos.nombre_funcionario
 * @returns {Object}
 * 
 */

function validarCrearSolicitud(datos) {
  const {
    tiene_periodos = false,
    tiene_periodos_disponibles = false,
    tiene_solicitud_activa = false,
    solicitud_activa_codigo = '',
    tiene_reintegro_en_curso = false,
    nombre_funcionario = ''
  } = datos;

  const prefijo = nombre_funcionario ? `El(la) funcionario(a) <strong>${nombre_funcionario}</strong> ` : '';

  if (!tiene_periodos) {
    return {
      puede_crear: false,
      mensaje: `${prefijo}No tiene periodos vacacionales registrados en el sistema. Contacte al administrador para que registre su(s) periodo(s) vacacional(es).`,
      tipo: 'error',
      titulo: '¡Atención!'
    };
  }

  if (!tiene_periodos_disponibles) {
    return {
      puede_crear: false,
      mensaje: `${prefijo}No tienes ningún pasivo vacacional en este momento. Para crear una nueva solicitud, debes tener periodos registrados en el sistema.`,
      tipo: 'warning',
      titulo: '¡No tienes días disponibles!'
    };
  }

  if (tiene_solicitud_activa) {
    const codigoTexto = solicitud_activa_codigo ? ` (${solicitud_activa_codigo})` : '';
    return {
      puede_crear: false,
      mensaje: `${prefijo}Ya tiene una solicitud de vacaciones en curso${codigoTexto}. Debe culminar el disfrute del periodo actual antes de crear una nueva solicitud.`,
      tipo: 'warning',
      titulo: '¡Solicitud en curso!'
    };
  }

  if (tiene_reintegro_en_curso) {
    return {
      puede_crear: false,
      mensaje: `${prefijo}Tiene una solicitud de reintegro de vacaciones en curso. Debe completar el proceso de reintegro antes de crear una nueva solicitud de vacaciones.`,
      tipo: 'warning',
      titulo: 'Reintegro en curso'
    };
  }

  return {
    puede_crear: true,
    mensaje: '',
    tipo: 'success',
    titulo: ''
  };
}

/**
 * @param {Object} resultado
 */

function mostrarAlertaValidacion(resultado) {
  Swal.fire({
    icon: resultado.tipo,
    title: resultado.titulo,
    html: resultado.mensaje,
    confirmButtonText: 'OK'
  });
}
