// Dynamically update subtotal in ExpenseProductInline
(function() {
    function updateSubtotal(row) {
        var productSelect = row.querySelector('select[id$="-product"]');
        var quantityInput = row.querySelector('input[id$="-quantity"]');
        var subtotalCell = row.querySelector('.field-subtotal');
        if (!productSelect || !quantityInput || !subtotalCell) return;

        var price = 0;
        var selectedOption = productSelect.options[productSelect.selectedIndex];
        if (selectedOption && selectedOption.getAttribute('data-price')) {
            price = parseFloat(selectedOption.getAttribute('data-price')) || 0;
        }
        var quantity = parseInt(quantityInput.value) || 0;
        var subtotal = price * quantity;
        subtotalCell.textContent = subtotal ? subtotal.toFixed(2) : '-';
    }

    function attachListeners() {
        var rows = document.querySelectorAll('.dynamic-expense_products');
        rows.forEach(function(row) {
            var productSelect = row.querySelector('select[id$="-product"]');
            var quantityInput = row.querySelector('input[id$="-quantity"]');
            if (productSelect) {
                productSelect.addEventListener('change', function() {
                    updateSubtotal(row);
                });
            }
            if (quantityInput) {
                quantityInput.addEventListener('input', function() {
                    updateSubtotal(row);
                });
            }
            // Initial update
            updateSubtotal(row);
        });
    }

    // Add data-price to product options
    function injectPrices() {
        var selects = document.querySelectorAll('select[id$="-product"]');
        selects.forEach(function(select) {
            for (var i = 0; i < select.options.length; i++) {
                var option = select.options[i];
                var price = option.text.match(/\((\d+\.\d{2})\)$/);
                if (price) {
                    option.setAttribute('data-price', price[1]);
                }
            }
        });
    }

    document.addEventListener('DOMContentLoaded', function() {
        injectPrices();
        attachListeners();
    });
})();
