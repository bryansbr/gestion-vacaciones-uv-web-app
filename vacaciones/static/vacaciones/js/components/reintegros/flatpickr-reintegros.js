(function () {
  const configurarFlatpickr = (selector, opciones = {}) => {
    const elementos = document.querySelectorAll(selector);
    if (typeof flatpickr === 'undefined' || !elementos.length) {
      return;
    }

    elementos.forEach((input) => {
      if (input.dataset.fpInitialized === '1') {
        return;
      }

      flatpickr(input, Object.assign({
        dateFormat: 'd/m/Y',
        allowInput: true
      }, opciones));

      input.dataset.fpInitialized = '1';
    });
  };

  document.addEventListener('DOMContentLoaded', () => {
    configurarFlatpickr('.flatpickr-input');
  });
})();
