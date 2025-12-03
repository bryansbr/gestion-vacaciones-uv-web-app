function obtenerDatosReportes() {
  const contenedorDatos = document.getElementById('datos-reportes');
  if (!contenedorDatos) {
    return {
      datosEstadosSolicitudes: { aprobadas: 0, autorizadas: 0, pendientes: 0, rechazadas: 0, devueltas: 0 },
      datosEstadosReintegros: { aprobados: 0, autorizados: 0, pendientes: 0, rechazados: 0, devueltos: 0 },
      datosAniosSolicitudes: [],
      datosFacultadesSolicitudes: [],
      datosAniosReintegros: [],
      datosFacultadesReintegros: [],
      datosReintegrosAnticipados: {}
    };
  }

  try {
    const datosEstadosSolicitudes = JSON.parse(contenedorDatos.getAttribute('data-estados-solicitudes') || '{}');
    const datosEstadosReintegros = JSON.parse(contenedorDatos.getAttribute('data-estados-reintegros') || '{}');
    const datosAniosSolicitudes = JSON.parse(contenedorDatos.getAttribute('data-anios-solicitudes') || '[]');
    const datosFacultadesSolicitudes = JSON.parse(contenedorDatos.getAttribute('data-facultades-solicitudes') || '[]');
    const datosAniosReintegros = JSON.parse(contenedorDatos.getAttribute('data-anios-reintegros') || '[]');
    const datosFacultadesReintegros = JSON.parse(contenedorDatos.getAttribute('data-facultades-reintegros') || '[]');
    const datosReintegrosAnticipados = JSON.parse(contenedorDatos.getAttribute('data-reintegros-anticipados') || '{}');

    return {
      datosEstadosSolicitudes,
      datosEstadosReintegros,
      datosAniosSolicitudes,
      datosFacultadesSolicitudes,
      datosAniosReintegros,
      datosFacultadesReintegros,
      datosReintegrosAnticipados
    };
  } catch (error) {
    return {
      datosEstadosSolicitudes: { aprobadas: 0, autorizadas: 0, pendientes: 0, rechazadas: 0, devueltas: 0 },
      datosEstadosReintegros: { aprobados: 0, autorizados: 0, pendientes: 0, rechazados: 0, devueltos: 0 },
      datosAniosSolicitudes: [],
      datosFacultadesSolicitudes: [],
      datosAniosReintegros: [],
      datosFacultadesReintegros: [],
      datosReintegrosAnticipados: {}
    };
  }
}

document.addEventListener('DOMContentLoaded', function() {
  const datos = obtenerDatosReportes();

  window.datosEstadosSolicitudes = datos.datosEstadosSolicitudes;
  window.datosEstadosReintegros = datos.datosEstadosReintegros;
  window.datosAniosSolicitudes = datos.datosAniosSolicitudes;
  window.datosFacultadesSolicitudes = datos.datosFacultadesSolicitudes;
  window.datosAniosReintegros = datos.datosAniosReintegros;
  window.datosFacultadesReintegros = datos.datosFacultadesReintegros;
  window.datosReintegrosAnticipados = datos.datosReintegrosAnticipados;
  
  inicializarGraficoEstadosCircular();
  inicializarGraficoEstadosDona();
  inicializarGraficoEstadosBarras();
  inicializarGraficoAniosSolicitudes();
  inicializarGraficoFacultadesSolicitudes();
  inicializarGraficoAniosEstadosSolicitudes();
  
  inicializarGraficoEstadosCircularReintegros();
  inicializarGraficoEstadosDonaReintegros();
  inicializarGraficoEstadosBarrasReintegros();
  inicializarGraficoAniosReintegros();
  inicializarGraficoFacultadesReintegros();
  inicializarGraficoAniosEstadosReintegros();
  inicializarGraficoReintegrosAnticipados();
});

function inicializarGraficoEstadosCircular() {
  const ctx = document.getElementById('grafico-estados-circular');
  if (!ctx) return;

  const datosEstados = window.datosEstadosSolicitudes || {
    aprobadas: 0,
    autorizadas: 0,
    pendientes: 0,
    rechazadas: 0,
    devueltas: 0,
  };

  const total = Object.values(datosEstados).reduce((a, b) => a + b, 0);
  
  if (total === 0) {
    ctx.parentElement.innerHTML = '<p class="text-gray-500 text-center py-20">No hay datos disponibles</p>';
    return;
  }

  new Chart(ctx, {
    type: 'pie',
    data: {
      labels: ['Aprobadas', 'Autorizadas', 'Pendientes', 'Rechazadas', 'Devueltas'],
      datasets: [{
        label: 'Solicitudes por Estado',
        data: [
          datosEstados.aprobadas,
          datosEstados.autorizadas,
          datosEstados.pendientes,
          datosEstados.rechazadas,
          datosEstados.devueltas
        ],
        backgroundColor: [
          'rgba(34, 197, 94, 0.8)',
          'rgba(59, 130, 246, 0.8)',
          'rgba(234, 179, 8, 0.8)',
          'rgba(239, 68, 68, 0.8)',
          'rgba(249, 115, 22, 0.8)'
        ],
        borderColor: [
          'rgba(34, 197, 94, 1)',
          'rgba(59, 130, 246, 1)',
          'rgba(234, 179, 8, 1)',
          'rgba(239, 68, 68, 1)',
          'rgba(249, 115, 22, 1)'
        ],
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const label = context.label || '';
              const value = context.parsed || 0;
              const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
              return `${label}: ${value} (${percentage}%)`;
            }
          }
        }
      }
    }
  });
}

function inicializarGraficoEstadosDona() {
  const ctx = document.getElementById('grafico-estados-dona');
  if (!ctx) return;

  const datosEstados = window.datosEstadosSolicitudes || {
    aprobadas: 0,
    autorizadas: 0,
    pendientes: 0,
    rechazadas: 0,
    devueltas: 0,
  };

  const total = Object.values(datosEstados).reduce((a, b) => a + b, 0);
  if (total === 0) {
    ctx.parentElement.innerHTML = '<p class="text-gray-500 text-center py-20">No hay datos disponibles</p>';
    return;
  }

  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Aprobadas', 'Autorizadas', 'Pendientes', 'Rechazadas', 'Devueltas'],
      datasets: [{
        label: 'Solicitudes por Estado',
        data: [
          datosEstados.aprobadas,
          datosEstados.autorizadas,
          datosEstados.pendientes,
          datosEstados.rechazadas,
          datosEstados.devueltas
        ],
        backgroundColor: [
          'rgba(34, 197, 94, 0.8)',
          'rgba(59, 130, 246, 0.8)',
          'rgba(234, 179, 8, 0.8)',
          'rgba(239, 68, 68, 0.8)',
          'rgba(249, 115, 22, 0.8)'
        ],
        borderColor: [
          'rgba(34, 197, 94, 1)',
          'rgba(59, 130, 246, 1)',
          'rgba(234, 179, 8, 1)',
          'rgba(239, 68, 68, 1)',
          'rgba(249, 115, 22, 1)'
        ],
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const label = context.label || '';
              const value = context.parsed || 0;
              const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
              return `${label}: ${value} (${percentage}%)`;
            }
          }
        }
      }
    }
  });
}

function inicializarGraficoEstadosBarras() {
  const ctx = document.getElementById('grafico-estados-barras');
  if (!ctx) return;

  const datosEstados = window.datosEstadosSolicitudes || {
    aprobadas: 0,
    autorizadas: 0,
    pendientes: 0,
    rechazadas: 0,
    devueltas: 0,
  };

  const total = Object.values(datosEstados).reduce((a, b) => a + b, 0);
  if (total === 0) {
    ctx.parentElement.innerHTML = '<p class="text-gray-500 text-center py-20">No hay datos disponibles</p>';
    return;
  }

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Aprobadas', 'Autorizadas', 'Pendientes', 'Rechazadas', 'Devueltas'],
      datasets: [{
        label: 'Cantidad de Solicitudes',
        data: [
          datosEstados.aprobadas,
          datosEstados.autorizadas,
          datosEstados.pendientes,
          datosEstados.rechazadas,
          datosEstados.devueltas
        ],
        backgroundColor: [
          'rgba(34, 197, 94, 0.8)',
          'rgba(59, 130, 246, 0.8)',
          'rgba(234, 179, 8, 0.8)',
          'rgba(239, 68, 68, 0.8)',
          'rgba(249, 115, 22, 0.8)'
        ],
        borderColor: [
          'rgba(34, 197, 94, 1)',
          'rgba(59, 130, 246, 1)',
          'rgba(234, 179, 8, 1)',
          'rgba(239, 68, 68, 1)',
          'rgba(249, 115, 22, 1)'
        ],
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            stepSize: 1
          }
        }
      },
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return `${context.parsed.y} solicitudes`;
            }
          }
        }
      }
    }
  });
}

function inicializarGraficoAniosSolicitudes() {
  const ctx = document.getElementById('grafico-anios-solicitudes');
  if (!ctx) return;

  const datosAnios = window.datosAniosSolicitudes || [];

  if (datosAnios.length === 0) {
    ctx.parentElement.innerHTML = '<p class="text-gray-500 text-center py-20">No hay datos disponibles</p>';
    return;
  }

  const anios = datosAnios.map(item => item.anio).sort();
  const totales = anios.map(anio => {
    const item = datosAnios.find(d => d.anio === anio);
    return item ? item.total : 0;
  });

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: anios.map(a => a.toString()),
      datasets: [{
        label: 'Total de Solicitudes',
        data: totales,
        backgroundColor: 'rgba(59, 130, 246, 0.8)',
        borderColor: 'rgba(59, 130, 246, 1)',
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            stepSize: 1
          }
        }
      },
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return `Total: ${context.parsed.y} solicitudes`;
            }
          }
        }
      }
    }
  });
}

function inicializarGraficoFacultadesSolicitudes() {
  const ctx = document.getElementById('grafico-facultades-solicitudes');
  if (!ctx) return;

  const datosFacultades = window.datosFacultadesSolicitudes || [];

  if (datosFacultades.length === 0) {
    ctx.parentElement.innerHTML = '<p class="text-gray-500 text-center py-20">No hay datos disponibles</p>';
    return;
  }

  const facultades = datosFacultades.map(item => item.facultad);
  const aprobadas = datosFacultades.map(item => item.por_estado.aprobado || 0);
  const autorizadas = datosFacultades.map(item => item.por_estado.autorizada || 0);
  const pendientes = datosFacultades.map(item => item.por_estado.pendiente || 0);
  const rechazadas = datosFacultades.map(item => item.por_estado.rechazado || 0);
  const devueltas = datosFacultades.map(item => item.por_estado.devuelta || 0);

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: facultades,
      datasets: [
        {
          label: 'Aprobadas',
          data: aprobadas,
          backgroundColor: 'rgba(34, 197, 94, 0.8)',
          borderColor: 'rgba(34, 197, 94, 1)',
          borderWidth: 1
        },
        {
          label: 'Autorizadas',
          data: autorizadas,
          backgroundColor: 'rgba(59, 130, 246, 0.8)',
          borderColor: 'rgba(59, 130, 246, 1)',
          borderWidth: 1
        },
        {
          label: 'Pendientes',
          data: pendientes,
          backgroundColor: 'rgba(234, 179, 8, 0.8)',
          borderColor: 'rgba(234, 179, 8, 1)',
          borderWidth: 1
        },
        {
          label: 'Rechazadas',
          data: rechazadas,
          backgroundColor: 'rgba(239, 68, 68, 0.8)',
          borderColor: 'rgba(239, 68, 68, 1)',
          borderWidth: 1
        },
        {
          label: 'Devueltas',
          data: devueltas,
          backgroundColor: 'rgba(249, 115, 22, 0.8)',
          borderColor: 'rgba(249, 115, 22, 1)',
          borderWidth: 1
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          stacked: false,
        },
        y: {
          beginAtZero: true,
          stacked: false,
          ticks: {
            stepSize: 1
          }
        }
      },
      plugins: {
        legend: {
          position: 'bottom',
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return `${context.dataset.label}: ${context.parsed.y}`;
            }
          }
        }
      }
    }
  });
}

function inicializarGraficoAniosEstadosSolicitudes() {
  const ctx = document.getElementById('grafico-anios-estados-solicitudes');
  if (!ctx) return;

  const datosAnios = window.datosAniosSolicitudes || [];

  if (datosAnios.length === 0) {
    ctx.parentElement.innerHTML = '<p class="text-gray-500 text-center py-20">No hay datos disponibles</p>';
    return;
  }

  const anios = datosAnios.map(item => item.anio).sort();
  const estados = ['aprobado', 'autorizada', 'pendiente', 'rechazado', 'devuelta'];
  const labelsEstados = ['Aprobadas', 'Autorizadas', 'Pendientes', 'Rechazadas', 'Devueltas'];
  const colores = [
    'rgba(34, 197, 94, 0.8)',
    'rgba(59, 130, 246, 0.8)',
    'rgba(234, 179, 8, 0.8)',
    'rgba(239, 68, 68, 0.8)',
    'rgba(249, 115, 22, 0.8)'
  ];

  const datasets = estados.map((estado, index) => {
    const datos = anios.map(anio => {
      const item = datosAnios.find(d => d.anio === anio);
      if (!item || !item.por_estado) return 0;
      return item.por_estado[estado] || 0;
    });

    return {
      label: labelsEstados[index],
      data: datos,
      backgroundColor: colores[index],
      borderColor: colores[index].replace('0.8', '1'),
      borderWidth: 1
    };
  });

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: anios.map(a => a.toString()),
      datasets: datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          stacked: false,
        },
        y: {
          beginAtZero: true,
          stacked: false,
          ticks: {
            stepSize: 1
          }
        }
      },
      plugins: {
        legend: {
          position: 'bottom',
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return `${context.dataset.label}: ${context.parsed.y}`;
            }
          }
        }
      }
    }
  });
}

function inicializarGraficoEstadosCircularReintegros() {
  const ctx = document.getElementById('grafico-estados-circular-reintegros');
  if (!ctx) return;

  const datosEstados = window.datosEstadosReintegros || {
    aprobados: 0,
    autorizados: 0,
    pendientes: 0,
    rechazados: 0,
    devueltos: 0,
  };

  const total = Object.values(datosEstados).reduce((a, b) => a + b, 0);
  
  if (total === 0) {
    ctx.parentElement.innerHTML = '<p class="text-gray-500 text-center py-20">No hay datos disponibles</p>';
    return;
  }

  new Chart(ctx, {
    type: 'pie',
    data: {
      labels: ['Aprobados', 'Autorizados', 'Pendientes', 'Rechazados', 'Devueltos'],
      datasets: [{
        label: 'Reintegros por Estado',
        data: [
          datosEstados.aprobados,
          datosEstados.autorizados,
          datosEstados.pendientes,
          datosEstados.rechazados,
          datosEstados.devueltos
        ],
        backgroundColor: [
          'rgba(34, 197, 94, 0.8)',
          'rgba(59, 130, 246, 0.8)',
          'rgba(234, 179, 8, 0.8)',
          'rgba(239, 68, 68, 0.8)',
          'rgba(249, 115, 22, 0.8)'
        ],
        borderColor: [
          'rgba(34, 197, 94, 1)',
          'rgba(59, 130, 246, 1)',
          'rgba(234, 179, 8, 1)',
          'rgba(239, 68, 68, 1)',
          'rgba(249, 115, 22, 1)'
        ],
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const label = context.label || '';
              const value = context.parsed || 0;
              const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
              return `${label}: ${value} (${percentage}%)`;
            }
          }
        }
      }
    }
  });
}

function inicializarGraficoEstadosDonaReintegros() {
  const ctx = document.getElementById('grafico-estados-dona-reintegros');
  if (!ctx) return;

  const datosEstados = window.datosEstadosReintegros || {
    aprobados: 0,
    autorizados: 0,
    pendientes: 0,
    rechazados: 0,
    devueltos: 0,
  };

  const total = Object.values(datosEstados).reduce((a, b) => a + b, 0);
  if (total === 0) {
    ctx.parentElement.innerHTML = '<p class="text-gray-500 text-center py-20">No hay datos disponibles</p>';
    return;
  }

  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Aprobados', 'Autorizados', 'Pendientes', 'Rechazados', 'Devueltos'],
      datasets: [{
        label: 'Reintegros por Estado',
        data: [
          datosEstados.aprobados,
          datosEstados.autorizados,
          datosEstados.pendientes,
          datosEstados.rechazados,
          datosEstados.devueltos
        ],
        backgroundColor: [
          'rgba(34, 197, 94, 0.8)',
          'rgba(59, 130, 246, 0.8)',
          'rgba(234, 179, 8, 0.8)',
          'rgba(239, 68, 68, 0.8)',
          'rgba(249, 115, 22, 0.8)'
        ],
        borderColor: [
          'rgba(34, 197, 94, 1)',
          'rgba(59, 130, 246, 1)',
          'rgba(234, 179, 8, 1)',
          'rgba(239, 68, 68, 1)',
          'rgba(249, 115, 22, 1)'
        ],
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const label = context.label || '';
              const value = context.parsed || 0;
              const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
              return `${label}: ${value} (${percentage}%)`;
            }
          }
        }
      }
    }
  });
}

function inicializarGraficoEstadosBarrasReintegros() {
  const ctx = document.getElementById('grafico-estados-barras-reintegros');
  if (!ctx) return;

  const datosEstados = window.datosEstadosReintegros || {
    aprobados: 0,
    autorizados: 0,
    pendientes: 0,
    rechazados: 0,
    devueltos: 0,
  };

  const total = Object.values(datosEstados).reduce((a, b) => a + b, 0);
  if (total === 0) {
    ctx.parentElement.innerHTML = '<p class="text-gray-500 text-center py-20">No hay datos disponibles</p>';
    return;
  }

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Aprobados', 'Autorizados', 'Pendientes', 'Rechazados', 'Devueltos', 'Completados', 'Cancelados'],
      datasets: [{
        label: 'Cantidad de Reintegros',
        data: [
          datosEstados.aprobados,
          datosEstados.autorizados,
          datosEstados.pendientes,
          datosEstados.rechazados,
          datosEstados.devueltos,
          datosEstados.completados,
          datosEstados.cancelados
        ],
        backgroundColor: [
          'rgba(34, 197, 94, 0.8)',
          'rgba(59, 130, 246, 0.8)',
          'rgba(234, 179, 8, 0.8)',
          'rgba(239, 68, 68, 0.8)',
          'rgba(249, 115, 22, 0.8)',
          'rgba(139, 92, 246, 0.8)',
          'rgba(107, 114, 128, 0.8)'
        ],
        borderColor: [
          'rgba(34, 197, 94, 1)',
          'rgba(59, 130, 246, 1)',
          'rgba(234, 179, 8, 1)',
          'rgba(239, 68, 68, 1)',
          'rgba(249, 115, 22, 1)',
          'rgba(139, 92, 246, 1)',
          'rgba(107, 114, 128, 1)'
        ],
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            stepSize: 1
          }
        }
      },
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return `${context.parsed.y} reintegros`;
            }
          }
        }
      }
    }
  });
}

function inicializarGraficoAniosReintegros() {
  const ctx = document.getElementById('grafico-anios-reintegros');
  if (!ctx) return;

  const datosAnios = window.datosAniosReintegros || [];

  if (datosAnios.length === 0) {
    ctx.parentElement.innerHTML = '<p class="text-gray-500 text-center py-20">No hay datos disponibles</p>';
    return;
  }

  const anios = datosAnios.map(item => item.anio).sort();
  const totales = anios.map(anio => {
    const item = datosAnios.find(d => d.anio === anio);
    return item ? item.total : 0;
  });

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: anios.map(a => a.toString()),
      datasets: [{
        label: 'Total de Reintegros',
        data: totales,
        backgroundColor: 'rgba(59, 130, 246, 0.8)',
        borderColor: 'rgba(59, 130, 246, 1)',
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            stepSize: 1
          }
        }
      },
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return `Total: ${context.parsed.y} reintegros`;
            }
          }
        }
      }
    }
  });
}

function inicializarGraficoFacultadesReintegros() {
  const ctx = document.getElementById('grafico-facultades-reintegros');
  if (!ctx) return;

  const datosFacultades = window.datosFacultadesReintegros || [];

  if (datosFacultades.length === 0) {
    ctx.parentElement.innerHTML = '<p class="text-gray-500 text-center py-20">No hay datos disponibles</p>';
    return;
  }

  const facultades = datosFacultades.map(item => item.facultad);
  const aprobados = datosFacultades.map(item => item.por_estado.aprobado || 0);
  const autorizados = datosFacultades.map(item => item.por_estado.autorizada || 0);
  const pendientes = datosFacultades.map(item => item.por_estado.pendiente || 0);
  const rechazados = datosFacultades.map(item => item.por_estado.rechazado || 0);
  const devueltos = datosFacultades.map(item => item.por_estado.devuelta || 0);

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: facultades,
      datasets: [
        {
          label: 'Aprobados',
          data: aprobados,
          backgroundColor: 'rgba(34, 197, 94, 0.8)',
          borderColor: 'rgba(34, 197, 94, 1)',
          borderWidth: 1
        },
        {
          label: 'Autorizados',
          data: autorizados,
          backgroundColor: 'rgba(59, 130, 246, 0.8)',
          borderColor: 'rgba(59, 130, 246, 1)',
          borderWidth: 1
        },
        {
          label: 'Pendientes',
          data: pendientes,
          backgroundColor: 'rgba(234, 179, 8, 0.8)',
          borderColor: 'rgba(234, 179, 8, 1)',
          borderWidth: 1
        },
        {
          label: 'Rechazados',
          data: rechazados,
          backgroundColor: 'rgba(239, 68, 68, 0.8)',
          borderColor: 'rgba(239, 68, 68, 1)',
          borderWidth: 1
        },
        {
          label: 'Devueltos',
          data: devueltos,
          backgroundColor: 'rgba(249, 115, 22, 0.8)',
          borderColor: 'rgba(249, 115, 22, 1)',
          borderWidth: 1
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          stacked: false,
        },
        y: {
          beginAtZero: true,
          stacked: false,
          ticks: {
            stepSize: 1
          }
        }
      },
      plugins: {
        legend: {
          position: 'bottom',
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return `${context.dataset.label}: ${context.parsed.y}`;
            }
          }
        }
      }
    }
  });
}

function inicializarGraficoAniosEstadosReintegros() {
  const ctx = document.getElementById('grafico-anios-estados-reintegros');
  if (!ctx) return;

  const datosAnios = window.datosAniosReintegros || [];

  if (datosAnios.length === 0) {
    ctx.parentElement.innerHTML = '<p class="text-gray-500 text-center py-20">No hay datos disponibles</p>';
    return;
  }

  const anios = datosAnios.map(item => item.anio).sort();
  const estados = ['aprobado', 'autorizada', 'pendiente', 'rechazado', 'devuelta'];
  const labelsEstados = ['Aprobados', 'Autorizados', 'Pendientes', 'Rechazados', 'Devueltos'];
  const colores = [
    'rgba(34, 197, 94, 0.8)',
    'rgba(59, 130, 246, 0.8)',
    'rgba(234, 179, 8, 0.8)',
    'rgba(239, 68, 68, 0.8)',
    'rgba(249, 115, 22, 0.8)'
  ];

  const datasets = estados.map((estado, index) => {
    const datos = anios.map(anio => {
      const item = datosAnios.find(d => d.anio === anio);
      if (!item || !item.por_estado) return 0;
      return item.por_estado[estado] || 0;
    });

    return {
      label: labelsEstados[index],
      data: datos,
      backgroundColor: colores[index],
      borderColor: colores[index].replace('0.8', '1'),
      borderWidth: 1
    };
  });

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: anios.map(a => a.toString()),
      datasets: datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          stacked: false,
        },
        y: {
          beginAtZero: true,
          stacked: false,
          ticks: {
            stepSize: 1
          }
        }
      },
      plugins: {
        legend: {
          position: 'bottom',
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return `${context.dataset.label}: ${context.parsed.y}`;
            }
          }
        }
      }
    }
  });
}

function inicializarGraficoReintegrosAnticipados() {
  const ctx = document.getElementById('grafico-reintegros-anticipados');
  if (!ctx) return;

  const datosReintegros = window.datosReintegrosAnticipados || {};

  const estadosConDatos = Object.entries(datosReintegros)
    .filter(([estado, cantidad]) => cantidad > 0)
    .map(([estado, cantidad]) => ({
      estado: estado.charAt(0).toUpperCase() + estado.slice(1),
      cantidad: cantidad
    }));

  if (estadosConDatos.length === 0) {
    ctx.parentElement.innerHTML = '<p class="text-gray-500 text-center py-20">No hay datos disponibles</p>';
    return;
  }

  const colores = [
    'rgba(34, 197, 94, 0.8)',
    'rgba(59, 130, 246, 0.8)',
    'rgba(234, 179, 8, 0.8)',
    'rgba(239, 68, 68, 0.8)',
    'rgba(249, 115, 22, 0.8)',
    'rgba(139, 92, 246, 0.8)',
    'rgba(236, 72, 153, 0.8)',
    'rgba(20, 184, 166, 0.8)'
  ];

  new Chart(ctx, {
    type: 'pie',
    data: {
      labels: estadosConDatos.map(item => item.estado),
      datasets: [{
        label: 'Reintegros Anticipados',
        data: estadosConDatos.map(item => item.cantidad),
        backgroundColor: colores.slice(0, estadosConDatos.length),
        borderColor: colores.slice(0, estadosConDatos.length).map(c => c.replace('0.8', '1')),
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const label = context.label || '';
              const value = context.parsed || 0;
              const total = estadosConDatos.reduce((a, b) => a + b.cantidad, 0);
              const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
              return `${label}: ${value} (${percentage}%)`;
            }
          }
        }
      }
    }
  });
}
