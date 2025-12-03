function obtenerDatosReporte() {
  const contenedorDatos = document.getElementById('datos-reporte-solicitudes');
  if (!contenedorDatos) {
    console.warn('Contenedor de datos no encontrado');
    return {
      datosEstados: { aprobadas: 0, autorizadas: 0, pendientes: 0, rechazadas: 0, devueltas: 0 },
      datosAnios: [],
      datosFacultades: []
    };
  }

  try {
    const estadosStr = contenedorDatos.getAttribute('data-estados') || '{}';
    const aniosStr = contenedorDatos.getAttribute('data-anios') || '[]';
    const facultadesStr = contenedorDatos.getAttribute('data-facultades') || '[]';
    
    if (!estadosStr || estadosStr.trim() === '' || estadosStr === '{}') {
      return {
        datosEstados: { aprobadas: 0, autorizadas: 0, pendientes: 0, rechazadas: 0, devueltas: 0 },
        datosAnios: [],
        datosFacultades: []
      };
    }
    
    const datosEstados = JSON.parse(estadosStr);
    const datosAnios = JSON.parse(aniosStr);
    const datosFacultades = JSON.parse(facultadesStr);

    return {
      datosEstados,
      datosAnios,
      datosFacultades
    };
  } catch (error) {
    console.error('Error al parsear datos del reporte:', error);
    console.error('Estados string:', contenedorDatos.getAttribute('data-estados'));
    console.error('Anios string:', contenedorDatos.getAttribute('data-anios'));
    console.error('Facultades string:', contenedorDatos.getAttribute('data-facultades'));
    return {
      datosEstados: { aprobadas: 0, autorizadas: 0, pendientes: 0, rechazadas: 0, devueltas: 0 },
      datosAnios: [],
      datosFacultades: []
    };
  }
}

function inicializarGraficoEstadosCircular() {
  const ctx = document.getElementById('grafico-estados-circular');
  if (!ctx) return;

  const { datosEstados } = obtenerDatosReporte();
  const total = Object.values(datosEstados).reduce((a, b) => a + b, 0);
  if (total === 0) return;

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

  const { datosEstados } = obtenerDatosReporte();
  const total = Object.values(datosEstados).reduce((a, b) => a + b, 0);
  if (total === 0) return;

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

  const { datosEstados } = obtenerDatosReporte();
  const total = Object.values(datosEstados).reduce((a, b) => a + b, 0);
  if (total === 0) return;

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

function inicializarGraficoAnios() {
  const ctx = document.getElementById('grafico-anios');
  if (!ctx) return;

  const { datosAnios } = obtenerDatosReporte();
  if (datosAnios.length === 0) return;

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

function inicializarGraficoAniosEstados() {
  const ctx = document.getElementById('grafico-anios-estados');
  if (!ctx) return;

  const { datosAnios } = obtenerDatosReporte();
  if (datosAnios.length === 0) return;

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

function inicializarGraficoFacultades() {
  const ctx = document.getElementById('grafico-facultades');
  if (!ctx) return;

  const { datosFacultades } = obtenerDatosReporte();
  if (datosFacultades.length === 0) return;

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

function inicializarTodosLosGraficos() {
  if (typeof Chart === 'undefined') {
    setTimeout(inicializarTodosLosGraficos, 100);
    return;
  }
  
  const contenedorDatos = document.getElementById('datos-reporte-solicitudes');
  if (!contenedorDatos) {
    setTimeout(inicializarTodosLosGraficos, 100);
    return;
  }
  
  inicializarGraficoEstadosCircular();
  inicializarGraficoEstadosDona();
  inicializarGraficoEstadosBarras();
  inicializarGraficoAnios();
  inicializarGraficoAniosEstados();
  inicializarGraficoFacultades();
}

window.inicializarTodosLosGraficos = inicializarTodosLosGraficos;

function inicializarGraficosCuandoEsteListo() {
  if (typeof inicializarTodosLosGraficos === 'function') {
    inicializarTodosLosGraficos();
  } else {
    window.addEventListener('load', function() {
      if (typeof inicializarTodosLosGraficos === 'function') {
        inicializarTodosLosGraficos();
      }
    });
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', function() {
    setTimeout(inicializarGraficosCuandoEsteListo, 300);
  });
} else {
  setTimeout(inicializarGraficosCuandoEsteListo, 300);
}
