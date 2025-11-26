$(document).ready(function() {
  const selectoresTablas = [
    '#tabla-solicitudes-funcionario',
    '#tabla-solicitudes-jefe',
    '#tabla-solicitudes-secretaria',
    '#tabla-solicitudes-coord',
    '#tabla-solicitudes-rrhh'
  ];
  
  let tabla = null;
  let tablaId = null;
  
  for (const selector of selectoresTablas) {
    const elemento = $(selector);
    if (elemento.length) {
      tabla = elemento;
      tablaId = selector.replace('#', '');
      break;
    }
  }
  
  if (!tabla || !tabla.length) {
    return;
  }

  registerDateSorting();

  const dataTable = tabla.DataTable({
    language: DATATABLES_SPANISH_LANGUAGE,
    pageLength: 5,
    lengthMenu: [[5, 10, 25, 50, 100, -1], [5, 10, 25, 50, 100, "Todos"]],
    order: [[7, 'desc']],
    searching: true,
    columnDefs: [
      {
        targets: -1,
        orderable: false,
        searchable: false,
        className: 'text-center',
        createdCell: function(td, cellData, rowData, row, col) {
          $(td).css('text-align', 'center');
        }
      },
      {
        targets: [2, 4, 7],
        type: 'date-dd-mm-yyyy'
      },
      {
        targets: [3],
        type: 'num'
      }
    ],
    responsive: true,
    dom: DATATABLES_DOM_LAYOUT,
    drawCallback: function() {
      $(`#${tablaId} tbody tr`).each(function(index) {
        if (index % 2 === 0) {
          $(this).css('background-color', '#ffffff');
        } else {
          $(this).css('background-color', '#f3f4f6');
        }
      });
    }
  });
});
