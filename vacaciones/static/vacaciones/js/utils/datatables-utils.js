const DATATABLES_SPANISH_LANGUAGE = {
    "decimal": "",
    "emptyTable": "No hay datos disponibles en la tabla",
    "info": "Mostrando _START_ a _END_ de _TOTAL_ entradas",
    "infoEmpty": "Mostrando 0 a 0 de 0 entradas",
    "infoFiltered": "(filtrado de _MAX_ entradas totales)",
    "infoPostFix": "",
    "thousands": ",",
    "lengthMenu": "Mostrar _MENU_ entradas",
    "loadingRecords": "Cargando...",
    "processing": "Procesando...",
    "search": "Buscar:",
    "zeroRecords": "No se encontraron registros coincidentes",
    "paginate": {
        "first": "Primero",
        "last": "Último",
        "next": "Siguiente",
        "previous": "Anterior"
    },
    "aria": {
        "sortAscending": ": activar para ordenar la columna de manera ascendente",
        "sortDescending": ": activar para ordenar la columna de manera descendente"
    }
};

function registerDateSorting() {
  if ($.fn.dataTable && $.fn.dataTable.ext && $.fn.dataTable.ext.type) {
    $.fn.dataTable.ext.type.order['date-dd-mm-yyyy-pre'] = function(data) {
      if (!data || typeof data !== 'string') return 0;
      const parts = data.trim().split('/');
      if (parts.length === 3) {
        const day = parseInt(parts[0], 10);
        const month = parseInt(parts[1], 10);
        const year = parseInt(parts[2], 10);
        if (!isNaN(day) && !isNaN(month) && !isNaN(year)) {
          return new Date(year, month - 1, day).getTime();
        }
      }
      return 0;
    };
  }
}

const DATATABLES_DOM_LAYOUT = '<"flex flex-wrap items-center justify-between mb-6 px-2"<"flex items-center gap-4"l><"flex items-center gap-4"f>>rt<"flex flex-wrap items-center justify-between mt-6 px-2"<"flex items-center gap-4"i><"flex items-center gap-4"p>>';

/**
 * Inicialización de DataTables
 * 
 * @param {string|jQuery} selector - Selector de la tabla
 * @param {object} options - Opciones adicionales para DataTables
 * @returns {DataTable} Instancia de DataTable inicializada
 */
function initDataTable(selector, options = {}) {
  const defaultOptions = {
    language: DATATABLES_SPANISH_LANGUAGE,
    pageLength: 10,
    lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "Todos"]],
    searching: true,
    responsive: true,
    dom: DATATABLES_DOM_LAYOUT
  };
    
  const mergedOptions = Object.assign({}, defaultOptions, options);

  registerDateSorting();
  
  return $(selector).DataTable(mergedOptions);
}
