$(document).ready(function() {
  const tabla = $('#tabla-periodos-vacacionales');
  
  if (!tabla.length) return;

  registerDateSorting();

  const dataTable = tabla.DataTable({
    language: DATATABLES_SPANISH_LANGUAGE,
    pageLength: 5,
    lengthMenu: [[5, 10, 25, 50, 100, -1], [5, 10, 25, 50, 100, "Todos"]],
    order: [[2, 'desc']],
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
        targets: [2, 3],
        type: 'date-dd-mm-yyyy'
      },
      {
        targets: [4, 5, 6],
        type: 'num'
      }
    ],
    responsive: true,
    dom: DATATABLES_DOM_LAYOUT,
    drawCallback: function() {
      $('#tabla-periodos-vacacionales tbody tr').each(function(index) {
        if (index % 2 === 0) {
          $(this).css('background-color', '#ffffff');
        } else {
          $(this).css('background-color', '#f3f4f6');
        }
      });
      
      setTimeout(function() {
        if (typeof window.inicializarConfirmacionEliminacionPeriodo === 'function') {
          window.inicializarConfirmacionEliminacionPeriodo();
        }
      }, 100);
    }
  });
});
