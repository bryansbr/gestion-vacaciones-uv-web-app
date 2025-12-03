function obtenerDatosReporte() {
  const contenedorDatos = document.getElementById('datos-reporte-reintegros');
  if (!contenedorDatos) {
    return {
      datosEstados: { aprobados: 0, autorizados: 0, pendientes: 0, rechazados: 0, devueltos: 0 },
      datosAnios: [],
      datosFacultades: [],
      datosReintegrosAnticipados: {}
    };
  }

  try {
    const estadosStr = contenedorDatos.getAttribute('data-estados') || '{}';
    const aniosStr = contenedorDatos.getAttribute('data-anios') || '[]';
    const facultadesStr = contenedorDatos.getAttribute('data-facultades') || '[]';
    const anticipadosStr = contenedorDatos.getAttribute('data-reintegros-anticipados') || '{}';
    
    if (!estadosStr || estadosStr.trim() === '' || estadosStr === '{}') {
      return {
        datosEstados: { aprobados: 0, autorizados: 0, pendientes: 0, rechazados: 0, devueltos: 0 },
        datosAnios: [],
        datosFacultades: [],
        datosReintegrosAnticipados: {}
      };
    }
    
    const datosEstados = JSON.parse(estadosStr);
    const datosAnios = JSON.parse(aniosStr);
    const datosFacultades = JSON.parse(facultadesStr);
    const datosReintegrosAnticipados = JSON.parse(anticipadosStr);

    return {
      datosEstados,
      datosAnios,
      datosFacultades,
      datosReintegrosAnticipados
    };
  } catch (error) {
    console.error('Error al parsear datos del reporte:', error);
    console.error('Estados string:', contenedorDatos.getAttribute('data-estados'));
    console.error('Anios string:', contenedorDatos.getAttribute('data-anios'));
    console.error('Facultades string:', contenedorDatos.getAttribute('data-facultades'));
    console.error('Anticipados string:', contenedorDatos.getAttribute('data-reintegros-anticipados'));
    return {
      datosEstados: { aprobados: 0, autorizados: 0, pendientes: 0, rechazados: 0, devueltos: 0 },
      datosAnios: [],
      datosFacultades: [],
      datosReintegrosAnticipados: {}
    };
  }
}

function inicializarGraficoEstadosCircularReintegros() {
  const ctx = document.getElementById('grafico-estados-circular-reintegros');
  if (!ctx) return;

  const { datosEstados } = obtenerDatosReporte();
  const total = Object.values(datosEstados).reduce((a, b) => a + b, 0);
  if (total === 0) return;

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

  const { datosEstados } = obtenerDatosReporte();
  const total = Object.values(datosEstados).reduce((a, b) => a + b, 0);
  if (total === 0) return;

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

  const { datosEstados } = obtenerDatosReporte();
  const total = Object.values(datosEstados).reduce((a, b) => a + b, 0);
  if (total === 0) return;

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

function inicializarGraficoAniosEstadosReintegros() {
  const ctx = document.getElementById('grafico-anios-estados-reintegros');
  if (!ctx) return;

  const { datosAnios } = obtenerDatosReporte();
  if (datosAnios.length === 0) return;

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

function inicializarGraficoFacultadesReintegros() {
  const ctx = document.getElementById('grafico-facultades-reintegros');
  if (!ctx) return;

  const { datosFacultades } = obtenerDatosReporte();
  if (datosFacultades.length === 0) return;

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

function inicializarGraficoReintegrosAnticipados() {
  const ctx = document.getElementById('grafico-reintegros-anticipados');
  if (!ctx) return;

  const { datosReintegrosAnticipados } = obtenerDatosReporte();
  const estadosConDatos = Object.entries(datosReintegrosAnticipados)
    .filter(([estado, cantidad]) => cantidad > 0)
    .map(([estado, cantidad]) => ({
      estado: estado.charAt(0).toUpperCase() + estado.slice(1),
      cantidad: cantidad
    }));

  if (estadosConDatos.length === 0) return;

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

function inicializarTodosLosGraficos() {
  if (typeof Chart === 'undefined') {
    setTimeout(inicializarTodosLosGraficos, 100);
    return;
  }
  
  const contenedorDatos = document.getElementById('datos-reporte-reintegros');
  if (!contenedorDatos) {
    setTimeout(inicializarTodosLosGraficos, 100);
    return;
  }
  
  inicializarGraficoEstadosCircularReintegros();
  inicializarGraficoEstadosDonaReintegros();
  inicializarGraficoEstadosBarrasReintegros();
  inicializarGraficoAniosReintegros();
  inicializarGraficoAniosEstadosReintegros();
  inicializarGraficoFacultadesReintegros();
  inicializarGraficoReintegrosAnticipados();
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
