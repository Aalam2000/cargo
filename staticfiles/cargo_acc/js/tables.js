// Функции для работы с таблицами

// Инициализация сортировки для таблицы
function initializeTableSort(tableHeaders, tableBodyId, defaultColumnIndex) {
    tableHeaders.forEach((header, index) => {
        header.addEventListener('click', function () {
            const currentSort = header.getAttribute('data-sort') || 'none';
            const isAscending = currentSort === 'asc';

            // Сброс сортировки для всех колонок
            tableHeaders.forEach(h => h.removeAttribute('data-sort'));

            // Устанавливаем атрибут сортировки для текущей колонки
            header.setAttribute('data-sort', isAscending ? 'desc' : 'asc');

            // Обновляем стрелки сортировки
            updateSortArrows(tableHeaders, header, !isAscending);

            // Сортировка таблицы
            sortTable(tableBodyId, index, !isAscending);
        });
    });

    // Инициализация сортировки по умолчанию
    sortTable(tableBodyId, defaultColumnIndex, true);
}

// Функция для сортировки таблицы
function sortTable(tableBodyId, columnIndex, isAscending) {
    const tableBody = document.getElementById(tableBodyId);
    const rows = Array.from(tableBody.querySelectorAll('tr'));

    rows.sort((rowA, rowB) => {
        const cellA = rowA.querySelectorAll('td')[columnIndex].innerText.toLowerCase();
        const cellB = rowB.querySelectorAll('td')[columnIndex].innerText.toLowerCase();

        if (cellA < cellB) return isAscending ? -1 : 1;
        if (cellA > cellB) return isAscending ? 1 : -1;
        return 0;
    });

    rows.forEach(row => tableBody.appendChild(row));  // Перерисовываем строки в нужном порядке
}

// Обновление стрелок сортировки
function updateSortArrows(tableHeaders, activeHeader, isAscending) {
    tableHeaders.forEach(h => {
        const arrow = h.querySelector('.sort-arrow');
        if (arrow) {
            arrow.innerText = h === activeHeader ? (isAscending ? '▲' : '▼') : '⇅';
        }
    });
}

// Добавление новой строки в таблицу
function addTableRow(tableBodyId, rowData) {
    const tableBody = document.getElementById(tableBodyId);
    const newRow = tableBody.insertRow();

    rowData.forEach(cellData => {
        const newCell = newRow.insertCell();
        newCell.innerText = cellData;
    });
}

// Удаление строки из таблицы
function deleteTableRow(tableBodyId, rowId) {
    const tableBody = document.getElementById(tableBodyId);
    const row = document.getElementById(rowId);
    if (row) {
        tableBody.removeChild(row);
    } else {
        console.error(`Строка с ID ${rowId} не найдена в таблице.`);
    }
}

// Фильтрация таблицы
function filterTable(tableBodyId, filterOptions) {
    const tableBody = document.getElementById(tableBodyId);
    const rows = Array.from(tableBody.querySelectorAll('tr'));

    rows.forEach(row => {
        let isVisible = true;

        filterOptions.forEach(option => {
            const cell = row.querySelector(`td:nth-child(${option.columnIndex})`);
            if (cell && !cell.innerText.toLowerCase().includes(option.value.toLowerCase())) {
                isVisible = false;
            }
        });

        row.style.display = isVisible ? '' : 'none';
    });
}
