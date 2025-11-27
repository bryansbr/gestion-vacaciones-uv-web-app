function validarCrearReintegro(datos) {
  const {
    tiene_solicitudes_autorizadas = false,
    nombre_funcionario = ''
  } = datos;

  const prefijo = nombre_funcionario ? `El(la) funcionario(a) <strong>${nombre_funcionario}</strong> ` : '';

  if (!tiene_solicitudes_autorizadas) {
    return {
      puede_crear: false,
      mensaje: `${prefijo}No tiene solicitudes de vacaciones autorizadas por Recursos Humanos disponibles para reintegro. Debe tener al menos una solicitud de vacaciones autorizada por RRHH (ya sea disfrutando de sus vacaciones o que haya completado todas sus vacaciones) para poder crear un reintegro.`,
      tipo: 'error',
      titulo: '¡Atención!'
    };
  }

  return {
    puede_crear: true,
    mensaje: '',
    tipo: 'success',
    titulo: ''
  };
}
