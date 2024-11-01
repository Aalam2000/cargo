document.addEventListener('DOMContentLoaded', function () {
    loadTableData('/cargo_acc/api/transport-bills/', 'bill-table', [
        'bill_code', 'departure_place', 'destination_place', 'shipping_date', 'delivery_date', 'carrier_company'
    ]);
    loadTableData('/cargo_acc/api/cargos/', 'cargo-table', [
        'cargo_code', 'client_code', 'weight', 'volume', 'cost', 'shipping_date', 'delivery_date', 'status'
    ]);
    loadTableData('/cargo_acc/api/products/', 'product-table', [
        'product_code', 'client_code', 'company', 'warehouse', 'cargo_type', 'weight', 'volume', 'cost', 'shipping_date', 'delivery_date'
    ]);
});

function loadTableData(apiUrl, tableId, columnsMap) {
    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById(tableId).querySelector('tbody');
            tableBody.innerHTML = '';

            data.forEach((item) => {
                const row = document.createElement('tr');
                row.classList.add('table-row');

                // Добавляем данные в таблицу по колонкам
                columnsMap.forEach((columnKey) => {
                    const cell = document.createElement('td');
                    const value = item[columnKey];
                    cell.textContent = value !== undefined && value !== null ? value : '';
                    row.appendChild(cell);
                });

                tableBody.appendChild(row);
            });
        })
        .catch(error => console.error('Ошибка загрузки данных:', error));
}
