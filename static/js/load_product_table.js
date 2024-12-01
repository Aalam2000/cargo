// Подключение необходимых метаданных таблицы
const tableMetadata = {
    'product-table': {
        tableId: 'product-table',
        headerTableId: 'product-table-h', // новый ID для заголовка
        bodyTableId: 'product-table-r',   // новый ID для тела
        apiPath: '/cargo_acc/api/products/',
        fields: [
            {name: 'product_code', label: 'Код Товара', type: 'CharField', visible: true},
            {name: 'client', label: 'Клиент', type: 'ForeignKey', relatedModel: 'clients', visible: true},
            {name: 'company', label: 'Компания', type: 'ForeignKey', relatedModel: 'companies', visible: true},
            {name: 'warehouse', label: 'Склад', type: 'ForeignKey', relatedModel: 'warehouses', visible: true},
            {name: 'record_date', label: 'Дата записи', type: 'DateField', visible: true},
            {name: 'cargo_description', label: 'Описание груза', type: 'CharField', visible: true},
            {name: 'cargo_type', label: 'Тип груза', type: 'ForeignKey', relatedModel: 'cargo-types', visible: true},
            {name: 'images', label: 'Фото груза', type: 'ManyToManyField', relatedModel: 'images', visible: true},
            {name: 'departure_place', label: 'Место отправления', type: 'CharField', visible: true},
            {name: 'destination_place', label: 'Место назначения', type: 'CharField', visible: true},
            {name: 'weight', label: 'Вес', type: 'DecimalField', visible: true},
            {name: 'volume', label: 'Объем', type: 'DecimalField', visible: true},
            {name: 'cost', label: 'Стоимость', type: 'DecimalField', visible: true},
            {name: 'insurance', label: 'Страховка', type: 'DecimalField', visible: true},
            {name: 'dimensions', label: 'Габариты', type: 'CharField', visible: true},
            {name: 'shipping_date', label: 'Дата отправки', type: 'DateField', visible: true},
            {name: 'delivery_date', label: 'Дата доставки', type: 'DateField', visible: true},
            {
                name: 'cargo_status',
                label: 'Статус груза',
                type: 'ForeignKey',
                relatedModel: 'cargo-statuses',
                visible: true
            },
            {
                name: 'packaging_type',
                label: 'Тип упаковки',
                type: 'ForeignKey',
                relatedModel: 'packaging-types',
                visible: true
            }
        ]
    }
};

// Функция для генерации заголовка таблицы
function generateTableHeader(tableData) {
    const thead = document.querySelector(`#${tableData.tableId}-h thead`);
    thead.innerHTML = '';

    const headerRow = document.createElement('tr');
    tableData.columnWidths = {}; // Хранение ширины колонок

    tableData.fields.filter(field => field.visible).forEach((field, index) => {
        const th = document.createElement('th');
        th.textContent = field.label;
        headerRow.appendChild(th);

        // После отрисовки заголовка сохраняем ширину
        setTimeout(() => {
            const computedStyle = window.getComputedStyle(th);
            const width = th.getBoundingClientRect().width; // Получаем точную ширину с плавающей точкой
            const padding = parseFloat(computedStyle.paddingLeft) + parseFloat(computedStyle.paddingRight);
            const border = parseFloat(computedStyle.borderLeftWidth) + parseFloat(computedStyle.borderRightWidth);
            tableData.columnWidths[field.name] = width; // Учитываем padding и border
        }, 0);
    });

    thead.appendChild(headerRow);
}

// Функция для загрузки данных таблицы
async function loadTableData(tableData) {
    const tableBody = document.querySelector(`#${tableData.tableId}-r tbody`);
    tableBody.innerHTML = '';

    try {
        const response = await fetch(tableData.apiPath);
        const data = await response.json();

        data.forEach(item => {
            const row = document.createElement('tr');
            row.classList.add('table-row');

            tableData.fields.filter(field => field.visible).forEach(field => {
                const td = document.createElement('td');
                td.textContent = item[field.name] || 'N/A';

                // Применяем сохранённую ширину
                const columnWidth = tableData.columnWidths[field.name];
                if (columnWidth) {
                    td.style.width = `${columnWidth}px`;
                    td.style.boxSizing = 'border-box'; // Учитываем границы и padding внутри ширины
                }

                row.appendChild(td);
            });

            tableBody.appendChild(row);
        });
    } catch (error) {
        console.error('Ошибка при загрузке данных:', error);
    }
}


// Инициализация таблицы при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    const productTableData = tableMetadata['product-table'];
    generateTableHeader(productTableData); // Создаем заголовок таблицы
    loadTableData(productTableData); // Загружаем и заполняем таблицу данными
    synchronizeColumnWidths();
});

function synchronizeColumnWidths() {
    const headerCells = document.querySelectorAll('#table-header th');
    const bodyCells = document.querySelectorAll('#table-body tr:first-child td');

    headerCells.forEach((headerCell, index) => {
        if (bodyCells[index]) {
            bodyCells[index].style.width = `${headerCell.offsetWidth}px`;
        }
    });
}