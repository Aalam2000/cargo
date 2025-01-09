// tiket: Подключение необходимых метаданных таблицы
const tableMetadata = {
    'product-table': {
        tableId: 'product-table',
        tableName: 'Таблица товаров',
        apiPath: '/cargo_acc/api/products/',
        apiDelPath: '/cargo_acc/api/delete/Product/',
        fields: [
            {name: 'product_code', label: 'Код Товара', type: 'CharField', visible: true},
            {name: 'client_code', label: 'Клиент', type: 'ForeignKey', relatedModel: 'clients', visible: true},
            {name: 'company_name', label: 'Компания', type: 'ForeignKey', relatedModel: 'companies', visible: true},
            {name: 'warehouse_name', label: 'Склад', type: 'ForeignKey', relatedModel: 'warehouses', visible: true},
            {name: 'record_date', label: 'Дата записи', type: 'DateField', visible: true},
            {name: 'cargo_description', label: 'Описание груза', type: 'CharField', visible: true},
            {
                name: 'cargo_type_name',
                label: 'Тип груза',
                type: 'ForeignKey',
                relatedModel: 'cargo-types',
                visible: true
            },
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
            {name: 'comment', label: 'Комментарий', type: 'CharField', visible: true},
            {
                name: 'cargo_status_name',
                label: 'Статус груза',
                type: 'ForeignKey',
                relatedModel: 'cargo-statuses',
                visible: true
            },
            {
                name: 'packaging_type_name',
                label: 'Тип упаковки',
                type: 'ForeignKey',
                relatedModel: 'packaging-types',
                visible: true
            }
        ]
    },
    'company-table': {
        tableId: 'company-table',
        tableName: 'Таблица компаний',
        apiPath: '/cargo_acc/api/companies/',
        apiDelPath: '/cargo_acc/api/delete/Company/',
        fields: [
            {name: 'name', label: 'Название', type: 'CharField', visible: true},
            {name: 'registration', label: 'Регистрационный номер', type: 'CharField', visible: true},
            {name: 'description', label: 'Описание', type: 'CharField', visible: true}
        ]
    },
    'client-table': {
        tableId: 'client-table',
        tableName: 'Таблица клиентов',
        apiPath: '/cargo_acc/api/clients/',
        apiDelPath: '/cargo_acc/api/delete/Client/',
        fields: [
            {name: 'id', label: 'ID', type: 'IntegerField', visible: false},
            {name: 'client_code', label: 'Код клиента', type: 'CharField', visible: true},
            {name: 'company', label: 'Компания', type: 'ForeignKey', relatedModel: 'companies', visible: true},
            {name: 'description', label: 'Описание', type: 'CharField', visible: true}
        ]
    },
    'warehouse-table': {
        tableId: 'warehouse-table',
        tableName: 'Таблица складов',
        apiPath: '/cargo_acc/api/warehouses/',
        apiDelPath: '/cargo_acc/api/delete/Warehouse/',
        fields: [
            {name: 'id', label: 'ID', type: 'IntegerField', visible: false},
            {name: 'name', label: 'Название', type: 'CharField', visible: true},
            {name: 'address', label: 'Адрес', type: 'CharField', visible: true},
            {name: 'company', label: 'Компания', type: 'ForeignKey', relatedModel: 'companies', visible: true}
        ]
    },
    'table-cargo-types': {
        tableId: 'table-cargo-types',
        tableName: 'Типы груза',
        apiPath: '/cargo_acc/api/cargo-types/',
        apiDelPath: '/cargo_acc/api/delete/CargoType/',
        fields: [
            {name: 'name', label: 'Название', type: 'CharField', visible: true},
            {name: 'description', label: 'Описание', type: 'CharField', visible: true}
        ]
    },
    'table-cargo-statuses': {
        tableId: 'table-cargo-statuses',
        tableName: 'Статусы груза',
        apiPath: '/cargo_acc/api/cargo-statuses/',
        apiDelPath: '/cargo_acc/api/delete/CargoStatus/',
        fields: [
            {name: 'name', label: 'Название', type: 'CharField', visible: true},
            {name: 'description', label: 'Описание', type: 'CharField', visible: true}
        ]
    },
    'table-packaging-types': {
        tableId: 'table-packaging-types',
        tableName: 'Типы упаковки',
        apiPath: '/cargo_acc/api/packaging-types/',
        apiDelPath: '/cargo_acc/api/delete/PackagingType/',
        fields: [
            {name: 'name', label: 'Название', type: 'CharField', visible: true},
            {name: 'description', label: 'Описание', type: 'CharField', visible: true}
        ]
    }
};


// Переменные для управления подгрузкой
let currentPage = 1; // Начальная страница (1 уже загружена)
let pageSize = 7; // Количество записей на страницу
let tableSettings = {}; // Настройка колонок таблицы

// Статический список обязательных полей для кнопки "Добавить"
const requiredFieldsForAdd = [
    'product_code',         // Код Товара
    'client_code',               // Клиент
    'company_name',              // Компания
    'warehouse_name',            // Склад
    'cargo_type_name',           // Тип груза
    'cargo_status_name',         // Статус груза
    'packaging_type_name',       // Тип упаковки
];

// tiket: Функция для генерации таблицы
// Функция для генерации таблицы
async function generateTable(tableData) {
    const table = document.querySelector(`#${tableData.tableId}`);
    const settings = tableSettings[tableData.tableId];

    if (!table) {
        console.error(`Таблица с ID "${tableData.tableId}" не найдена.`);
        return;
    }

    const thead = table.querySelector('thead');
    const tbody = table.querySelector('tbody');

    try {
        const response = await fetch(`${tableData.apiPath}?page=1&page_size=${pageSize}`);
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);

        const data = await response.json();
        const fragment = document.createDocumentFragment();

        // Очистка шапки
        thead.innerHTML = '';
        const headerRow = document.createElement('tr');

        // Заполнение шапки с проверкой настроек
        tableData.fields.forEach(field => {
            if (!settings || settings[field.name] !== false) { // Проверяем настройки
                const th = document.createElement('th');
                th.textContent = field.label;
                headerRow.appendChild(th);
            }
        });


        // Добавление колонки для удаления
        const deleteHeader = document.createElement('th');
        deleteHeader.innerHTML = '<i class="fa fa-trash"></i>';
        headerRow.appendChild(deleteHeader);

        thead.appendChild(headerRow);

        // Заполнение строк таблицы с проверкой настроек
        data.forEach(item => {
            const row = document.createElement('tr');
            row.setAttribute('data-id', item.id);

            tableData.fields.forEach(field => {
                if (!settings || settings[field.name] !== false) { // Проверяем настройки
                    const td = document.createElement('td');
                    td.textContent = item[field.name] || 'N/A';
                    row.appendChild(td);
                }
            });


            // Добавление кнопки удаления
            const deleteCell = document.createElement('td');
            deleteCell.classList.add('delete-cell');
            deleteCell.innerHTML = `<i class="fa fa-trash" data-id="${item.id}"></i>`;
            row.appendChild(deleteCell);

            fragment.appendChild(row);
        });


        tbody.innerHTML = '';
        tbody.appendChild(fragment);

    } catch (error) {
        console.error('Ошибка загрузки данных:', error);
        alert('Ошибка загрузки данных. Проверьте API или консоль разработчика.');
    }


}


// Заполним все таблицы


// Найти все элементы <table> на странице
const tableElements = document.querySelectorAll('table');

// Пройтись по каждой таблице
tableElements.forEach((tableElement) => {
    initializeTable(tableElement).catch(error => {
        console.error(`Ошибка при инициализации таблицы с ID "${tableElement.id}":`, error);
    });
});


// Заполняем таблицу
async function initializeTable(tableElement) {
    const tableId = tableElement.id;
    const metadata = tableMetadata[tableId];

    if (metadata) {
        await loadTableSettings(tableId); // Загрузка настроек
        generateTable(metadata);         // Генерация таблицы
    } else {
        console.error(`Метаданные для таблицы с ID "${tableId}" не найдены.`);
    }
}

// Слушатель на клики в таблицах
document.addEventListener('click', async (event) => {
    const container = event.target.closest('[data-table]');
    let tableId;
    let metadata;
    if (container) {
        tableId = container.dataset.table; // Получаем ID таблицы
        metadata = tableMetadata[tableId]; // Получаем метаданные таблицы
        if (!metadata) {
            console.error(`Метаданные для таблицы с ID "${tableId}" не найдены.`);
            return;
        }

        // Исключаем обработку кликов на заголовке таблицы (th)
        if (event.target.tagName === 'TH')
            return; // Прерываем выполнение, если клик был на th
    }

    if (event.target.closest('.delete-cell')) {
        const row = event.target.closest('tr');
        const rowId = row.dataset.id;
        const rowData = row.children[0]?.textContent || '';
        openDeleteModal(rowId, rowData, metadata.tableName, tableId);
        return;
    }

    if (event.target.matches('.add-button')) {
        const modalId = event.target.dataset.modal;
        openAddRowModal(modalId, metadata.tableName, tableId, null); // Передаем null для добавления новой строки
        return;
    }

    if (event.target.closest('.settings-button')) {
        const modalId = event.target.dataset.modal || 'settings-modal';
        openSettingsModal(modalId, metadata.tableName, tableId, tableMetadata[tableId]);
        return;
    }


    // Обработка клика по строке таблицы для редактирования
    const row = event.target.closest('tr');
    if (row) {
        const rowId = row.dataset.id;
        const rowData = Array.from(row.children).map((cell) => cell.textContent.trim());

        openAddRowModal('product-modal', metadata.tableName, tableId, {id: rowId, data: rowData}); // Передаем данные строки
    }
})
;


// Функция открытия модального окна
function openDeleteModal(rowId, productCode, tableName, tableId) {
    // Загружаем HTML модального окна, если оно ещё не добавлено
    if (!document.getElementById('delete-modal')) {
        fetch('/cargo_acc/mod_delrow')
            .then(response => response.text())
            .then(html => {
                document.body.insertAdjacentHTML('beforeend', html);
                showDeleteModal(rowId, productCode, tableName, tableId); // Показ модального окна
            });
    } else {
        showDeleteModal(rowId, productCode, tableName, tableId);
    }
}

function showDeleteModal(rowId, productCode, tableName, tableId) {
    const modal = document.getElementById('delete-modal');

    modal.style.display = 'block'; // Показываем окно
    document.body.classList.add('modal-open'); // Затемняем фон
    document.getElementById('delete-modal-title').textContent = 'Удаление строки';
    document.getElementById('delete-modal-body').textContent = `Вы действительно хотите удалить строку "${productCode}" из таблицы "${tableName}"?`;

    // Добавляем действия для кнопок
    document.getElementById('delete-close-modal').addEventListener('click', () => closeModal('delete-modal'));
    document.getElementById('delete-cancel-modal').addEventListener('click', () => closeModal('delete-modal'));

    // Передаем данные в confirm-delete
    const confirmDeleteButton = document.getElementById('delete-confirm-delete');
    confirmDeleteButton.onclick = () => deleteRow(tableId, rowId);
}

// Новая версия функции deleteRow, которая удаляет запись через тот же ViewSet (ProductViewSet),
// используя DELETE /cargo_acc/api/products/<itemId>/ и обновляет DOM

async function deleteRow(tableId, itemId) {
    const tableData = tableMetadata[tableId];
    if (!tableData) {
        console.error(`Метаданные для таблицы с ID "${tableId}" не найдены.`);
        return;
    }

    // Удаляем запись по /cargo_acc/api/products/<id>/ (или аналогичный путь из tableData.apiPath)
    try {
        const response = await fetch(`${tableData.apiPath}${itemId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });

        if (response.ok) {
            // Находим строку в таблице по ID и удаляем её из DOM
            const table = document.getElementById(tableData.tableId);
            const row = table.querySelector(`[data-id="${itemId}"]`);
            if (row) {
                row.remove();
            } else {
                console.warn(`Строка с ID ${itemId} не найдена в DOM.`);
            }
        } else {
            throw new Error('Ошибка при удалении элемента с сервера');
        }
    } catch (error) {
        console.error('Ошибка при удалении:', error);
    }

    // Закрываем модалку
    closeModal('delete-modal');
}


// Функция открытия модального окна добавления строки
function openAddRowModal(modalId, tableName, tableId, rowInfo = null) {
    if (!document.getElementById(modalId)) {
        fetch('/cargo_acc/mod_addrow')
            .then(response => response.text())
            .then(html => {
                document.body.insertAdjacentHTML('beforeend', html);
                showAddRowModal(modalId, tableName, tableId, rowInfo);
            });
    } else {
        showAddRowModal(modalId, tableName, tableId, rowInfo);
    }
}

let CurRowInfoGLOBAL = [];

function takeCurRowInfo() {
    if (CurRowInfoGLOBAL === null || (Array.isArray(CurRowInfoGLOBAL) && CurRowInfoGLOBAL.length === 0)) {
        return null;
    }
    return CurRowInfoGLOBAL.id;
}


async function showAddRowModal(modalId, tableName, tableId, rowInfo = null) {
    const modal = document.getElementById(modalId);
    const tableData = tableMetadata[tableId];
    console.log("Параметры для showAddRowModal:", {modalId, tableName, tableId, rowInfo});

    if (!tableData) {
        console.error(`Метаданные для таблицы ${tableId} не найдены.`);
        return;
    }

    // Режим редактирования
    const isEditMode = rowInfo !== null && rowInfo.id;

    // Заголовок
    document.getElementById('product-modal-title').textContent = isEditMode
        ? 'Изменение строки'
        : 'Добавление строки';

    // Очищаем модалку
    const modalBody = document.getElementById('product-modal-body');
    modalBody.innerHTML = '';

    // Форма
    const form = document.createElement('form');
    form.id = 'add-row-form';

    // Сетка
    const row = document.createElement('div');
    row.classList.add('d-grid');
    row.style.gridTemplateColumns = '1fr 1fr';
    row.style.gap = '1rem';
    let fieldsToDisplay;
    if (isEditMode) {
        // В режиме редактирования показываем все доступные поля
        fieldsToDisplay = [
            'product_code',
            'client_name',
            'comment',
            'warehouse_name',
            'company_name',
            'cargo_description'
        ];
    } else {
        // В режиме добавления показываем только обязательные поля
        fieldsToDisplay = requiredFieldsForAdd;
    }
    CurRowInfoGLOBAL = rowInfo;
    // Загружаем старые данные, если редактируем
    let productData = null;
    if (isEditMode) {
        try {
            const response = await fetch(`${tableData.apiPath}${rowInfo.id}/`);
            if (!response.ok) {
                console.log("rowInfo.id: ", rowInfo.id)
                throw new Error(`Ошибка загрузки записи с ID ${rowInfo.id}`);
            }
            productData = await response.json();
        } catch (error) {
            console.error('Ошибка при загрузке записи:', error);
            return;
        }
    }

    // Создаем поля
    tableData.fields.forEach((field) => {
        if (!fieldsToDisplay.includes(field.name)) return;

        const formGroup = document.createElement('div');
        formGroup.classList.add('form-group', 'flex-grow-1');

        const label = document.createElement('label');
        label.textContent = field.label;
        label.setAttribute('for', field.name);
        formGroup.appendChild(label);

        const input = document.createElement('input');
        input.type = 'text';
        input.name = field.name;
        input.id = field.name;
        input.classList.add('form-control');
        input.placeholder = field.placeholder || `Введите ${field.label.toLowerCase()}`;

        // Подставляем старое значение
        if (isEditMode && productData && productData[field.name] !== undefined) {
            input.value = productData[field.name] ? String(productData[field.name]) : '';
        }

        // Особый случай для поля Client (с бесконечным скроллом и фильтром)
        if (field.name === 'client_code') {
            const dropdown = document.createElement('div');
            dropdown.classList.add('dropdown-menu');
            dropdown.style.display = 'none';
            modalBody.appendChild(dropdown);

            input.addEventListener('input', () => {
                updateClientDropdownForID(input, dropdown);
            });
            input.addEventListener('focus', () => {
                updateClientDropdownForID(input, dropdown);
            });
            input.addEventListener('blur', () => {
                setTimeout(() => {
                    dropdown.style.display = 'none';
                }, 100);
            });
            document.addEventListener('click', (event) => {
                if (
                    !event.target.closest('.form-control') &&
                    !event.target.closest('.dropdown-menu')
                ) {
                    dropdown.style.display = 'none';
                }
            });

            // Остальные ForeignKey (склад, компания и т.д.)
        } else if (
            field.relatedModel &&
            ['companies', 'warehouses', 'cargo-types', 'cargo-statuses', 'packaging-types']
                .includes(field.relatedModel)
        ) {
            const dropdown = document.createElement('div');
            dropdown.classList.add('dropdown-menu');
            dropdown.style.display = 'none';
            modalBody.appendChild(dropdown);

            input.addEventListener('focus', async () => {
                await updateUniversalDropdownForID(input, dropdown, field.relatedModel);
                dropdown.style.display = 'block';
            });
            input.addEventListener('blur', () => {
                setTimeout(() => {
                    dropdown.style.display = 'none';
                }, 100);
            });
            document.addEventListener('click', (event) => {
                if (
                    !event.target.closest('.form-control') &&
                    !event.target.closest('.dropdown-menu')
                ) {
                    dropdown.style.display = 'none';
                }
            });
        }

        formGroup.appendChild(input);
        row.appendChild(formGroup);
    });

    form.appendChild(row);
    modalBody.appendChild(form);

    // Показываем модалку
    modal.style.display = 'block';
    document.body.classList.add('modal-open');

    // Обработчики кнопок
    if (!modal.dataset.listenersAdded) {
        document.getElementById('product-close-modal').addEventListener('click', () => closeModal(modalId));
        document.getElementById('product-cancel-modal').addEventListener('click', () => closeModal(modalId));
        // Сохранение
        document.getElementById('product-modal-save').addEventListener('click', async () => {

            const curRowInfo = takeCurRowInfo();

            // Сбор полей
            const patchData = {};

            fieldsToDisplay.forEach((fieldName) => {
                const inputEl = document.getElementById(fieldName);
                if (!inputEl) return;

                let newValue = inputEl.value.trim();
                // ForeignKey → берём ID из dataset.selectedId
                if (['client_code', 'warehouse_name', 'company_name', 'cargo_status_name', 'cargo_type_name', 'packaging_type_name'].includes(fieldName)) {
                    if (inputEl.dataset.selectedId) {
                        newValue = parseInt(inputEl.dataset.selectedId, 10);
                        if (isNaN(newValue)) {
                            return;
                        }
                    } else {

                        // Не выбрали новый → не трогаем
                        if (!isEditMode) {
                            // При добавлении: null
                            newValue = null;
                        } else {
                            // При редактировании: не добавляем поле в patchData
                            return;
                        }
                    }
                }
                if (isEditMode && productData) {
                    // Сравниваем со старым значением (частичное обновление)
                    const oldValue = productData[fieldName];
                    if (String(newValue) !== String(oldValue)) {
                        patchData[fieldName] = newValue;
                    }
                } else {
                    // При добавлении (POST) добавляем всё, что ввели
                    if (newValue !== '') {
                        patchData[fieldName] = newValue;
                    }
                }
            });

            if (isEditMode) {
                // Если нет изменений - ничего не отправляем
                if (Object.keys(patchData).length === 0) {
                    console.log('Нет изменений, PATCH не отправляем');
                } else {
                    const response = await fetch(`${tableData.apiPath}${curRowInfo}/`, {
                        method: 'PATCH',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCSRFToken()
                        },
                        body: JSON.stringify(patchData)
                    });
                    if (response.ok) {
                        const updatedItem = await response.json();
                        updateRowInTable(tableData, updatedItem, curRowInfo);
                        console.log('Редактирование завершено');
                    } else {
                        const errText = await response.text();
                        console.error('Ошибка PATCH:', response.status, errText);
                    }
                }
            } else {
                // Добавляем новую запись
                console.log("ПУТЬ: ", tableData.apiPath);
                console.log("Перед отправки: ", patchData);

                // Измените имена полей
                const correctedPatchData = {
                    product_code: patchData.product_code,
                    client_id: patchData.client_code,
                    company_id: patchData.company_name,
                    warehouse_id: patchData.warehouse_name,
                    cargo_type_id: patchData.cargo_type_name,
                    cargo_status_id: patchData.cargo_status_name,
                    packaging_type_id: patchData.packaging_type_name
                };

                const response = await fetch(`${tableData.apiPath}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken()
                    },
                    body: JSON.stringify(correctedPatchData)
                });
                console.log("После отправки: ", patchData);
                if (response.ok) {
                    const newItem = await response.json();
                    addRowToTable(tableData, newItem);
                    console.log('Добавление завершено');
                } else {
                    console.error('Ошибка при добавлении новой записи (POST)');
                }
            }

            closeModal(modalId);
        });
        modal.dataset.listenersAdded = 'true';
    }
}


// /**
//  * Обновляет существующую строку в таблице на экране (DOM).
//  * @param {Object} tableData - Метаданные таблицы (из tableMetadata[tableId]).
//  * @param {Object} updatedItem - Объект с обновлёнными данными (ответ сервера после PATCH).
//  * @param {number|string} itemId - Идентификатор строки, которую обновляем.
//  */
function updateRowInTable(tableData, updatedItem, itemId) {
    const table = document.getElementById(tableData.tableId);
    if (!table) {
        console.error(`Таблица с ID "${tableData.tableId}" не найдена.`);
        return;
    }

    // Находим строку по data-id
    const row = table.querySelector(`[data-id="${itemId}"]`);
    if (!row) {
        console.warn(`Строка с ID ${itemId} не найдена в DOM (updateRowInTable).`);
        return;
    }

    // Индекс ячейки (с учётом настроек видимости колонок)
    let cellIndex = 0;
    const settings = tableSettings[tableData.tableId] || {};

    // Проходимся по всем полям, как при generateTable
    tableData.fields.forEach((field) => {
        // Проверяем, не скрыто ли поле в настройках
        if (settings[field.name] === false) {
            return; // Пропускаем ячейку
        }

        // Находим нужную ячейку
        const cell = row.children[cellIndex];
        cellIndex++;

        // Подставляем новое значение или 'N/A'
        const newValue = updatedItem[field.name] || 'N/A';
        cell.textContent = newValue;
    });

    // Последняя ячейка (для удаления) обычно идёт после всех полей
    // Если у вас есть ещё какие-то специальные ячейки (например, кнопка редактирования),
    // нужно адаптировать логику cellIndex.
}

// /**
//  * Добавляет новую строку в таблицу (DOM).
//  * @param {Object} tableData - Метаданные таблицы (из tableMetadata[tableId]).
//  * @param {Object} newItem - Объект с новыми данными (ответ сервера после POST).
//  */
function addRowToTable(tableData, newItem) {
    const table = document.getElementById(tableData.tableId);
    if (!table) {
        console.error(`Таблица с ID "${tableData.tableId}" не найдена.`);
        return;
    }

    const tbody = table.querySelector('tbody');
    if (!tbody) {
        console.error(`tbody не найден в таблице ${tableData.tableId}`);
        return;
    }

    // Создаём новый <tr> и проставляем data-id
    const newRow = document.createElement('tr');
    newRow.setAttribute('data-id', newItem.id);

    // Индекс поля (с учётом настроек видимости)
    const settings = tableSettings[tableData.tableId] || {};

    tableData.fields.forEach((field) => {
        if (settings[field.name] === false) {
            return; // Не отображаем скрытые поля
        }

        const td = document.createElement('td');
        td.textContent = newItem[field.name] || 'N/A';
        newRow.appendChild(td);
    });

    // Добавляем ячейку для удаления (если в generateTable она тоже добавляется)
    const deleteCell = document.createElement('td');
    deleteCell.classList.add('delete-cell');
    // Здесь та же логика, что и в generateTable:
    deleteCell.innerHTML = `<i class="fa fa-trash" data-id="${newItem.id}"></i>`;
    newRow.appendChild(deleteCell);

    tbody.appendChild(newRow);
}


// /**
//  * Загружает список элементов (id + name) из /cargo_acc/api/<relatedModel>/,
//  * создает выпадающий список, при выборе элемента сохраняет item.id в input.dataset.selectedId
//  * и отображает item.name в input.value.
//  *
//  * @param {HTMLInputElement} inputElement - Поле ввода, куда записываем name и dataset.selectedId.
//  * @param {HTMLElement} dropdownElement - Контейнер для списка <div class="dropdown-menu">.
//  * @param {string} relatedModel - Название модели (companies, warehouses и т.д.).
//  */
async function updateUniversalDropdownForID(inputElement, dropdownElement, relatedModel) {
    dropdownElement.innerHTML = ''; // Очищаем старое содержимое

    try {
        // Запрос к API (например, /cargo_acc/api/warehouses/)
        const response = await fetch(`/cargo_acc/api/${relatedModel}/`);
        if (!response.ok) {
            throw new Error(`Ошибка API: ${response.status}`);
        }
        const data = await response.json();

        // Предположим, что data — это массив объектов, каждый имеет {id, name, ...}
        if (Array.isArray(data)) {
            data.forEach(item => {
                const option = document.createElement('div');
                option.classList.add('dropdown-item');
                option.textContent = item.name || 'Неизвестно';
                option.dataset.id = item.id;

                // При клике по варианту:
                option.addEventListener('click', () => {
                    // Показываем пользователю название
                    inputElement.value = item.name || '';
                    // Сохраняем ID в dataset (для отправки PATCH/POST)
                    inputElement.dataset.selectedId = item.id;
                    // Прячем выпадающий список
                    dropdownElement.style.display = 'none';
                });

                dropdownElement.appendChild(option);
            });
        } else {
            console.error("Некорректная структура данных для dropdown:", data);
        }

        // Позиционирование выпадающего списка
        const inputRect = inputElement.getBoundingClientRect();
        dropdownElement.style.position = 'absolute';
        dropdownElement.style.top = `${inputElement.offsetTop + inputElement.offsetHeight}px`;
        dropdownElement.style.left = `${inputElement.offsetLeft}px`;
        dropdownElement.style.width = `${inputElement.offsetWidth}px`;
        dropdownElement.style.zIndex = '1050';

        // Ограничение высоты и прокрутка
        dropdownElement.style.maxHeight = '200px';
        dropdownElement.style.overflowY = 'auto';

    } catch (error) {
        console.error(`Ошибка загрузки данных для модели "${relatedModel}":`, error);
    }
}


// Функция закрытия модального окна
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none'; // Скрываем окно
        document.body.classList.remove('modal-open'); // Убираем затемнение фона
        // Скрываем окно со списком клиентов
        const dropdown = document.querySelector('.dropdown-menu');
        if (dropdown) {
            dropdown.style.display = 'none'; // Скрываем выпадающий список
        }
    }
}


// Получаем CSRF-токен из cookies
function getCSRFToken() {
    const cookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
    return cookie ? decodeURIComponent(cookie.split('=')[1]) : null;
}


// Фильтрация (пример уже у вас есть):
async function filterClients(query, page = 1) {
    if (!query.trim() && page === 1) {
        // Если запрос пуст и это первая страница, возвращаем первые 7 клиентов из локального кэша
        return window.clientData.slice(0, 7);
    }

    try {
        // Выполняем серверный запрос с фильтром и пагинацией
        const response = await fetch(`/cargo_acc/api/get_clients/?search=${encodeURIComponent(query)}&page_size=7&page=${page}`);
        const data = await response.json();
        return data.results || [];
    } catch (error) {
        console.error("Ошибка фильтрации клиентов:", error);
        return [];
    }
}


// /**
//  * Обновлённая версия updateClientDropdown, которая:
//  *  - При вводе или фокусе показывает первые 7 записей (если поле пустое)
//  *    или отфильтрованные записи (если что-то введено).
//  *  - При прокрутке догружает следующие страницы (бесконечный скролл).
//  *  - При клике по варианту записывает client_code в input.value,
//  *    а client.id в input.dataset.selectedId, чтобы при сохранении отправлялся ID.
//  */
async function updateClientDropdownForID(inputElement, dropdownElement) {
    const query = inputElement.value.trim();  // Текущий ввод пользователя
    const filteredClients = await filterClients(query); // Загружаем первую страницу (до 7 записей)

    // Очищаем старые результаты
    dropdownElement.innerHTML = '';
    dropdownElement.dataset.currentPage = 1; // Устанавливаем текущую страницу = 1

    if (filteredClients.length === 0) {
        dropdownElement.style.display = 'none';
        return;
    }

    // Позиционируем dropdown относительно input
    const inputRect = inputElement.getBoundingClientRect();
    dropdownElement.style.position = 'absolute';
    dropdownElement.style.top = `${inputElement.offsetTop + inputElement.offsetHeight}px`;
    dropdownElement.style.left = `${inputElement.offsetLeft}px`;
    dropdownElement.style.width = `${inputElement.offsetWidth}px`;
    dropdownElement.style.zIndex = '1050';

    // Добавляем клиентов в список (первая страница)
    appendClientsToDropdownForID(filteredClients, dropdownElement, inputElement);

    // Показываем список
    dropdownElement.style.display = 'block';

    // Обработчик скролла для подгрузки следующих страниц
    const onScrollHandler = async function () {
        if (dropdownElement.scrollTop + dropdownElement.clientHeight >= dropdownElement.scrollHeight) {
            const nextPage = parseInt(dropdownElement.dataset.currentPage, 10) + 1;
            const additionalClients = await filterClients(query, nextPage);

            if (additionalClients.length > 0) {
                dropdownElement.dataset.currentPage = nextPage; // Обновляем текущую страницу
                appendClientsToDropdownForID(additionalClients, dropdownElement, inputElement);
            }
        }
    };

    // Снимаем предыдущий обработчик (если был), вешаем новый
    dropdownElement.removeEventListener('scroll', onScrollHandler);
    dropdownElement.addEventListener('scroll', onScrollHandler);
}

// /**
//  * Функция, которая добавляет клиентов (массив) во всплывающий список dropdownElement.
//  * При клике по элементу устанавливает:
//  *   inputElement.value = client.client_code
//  *   inputElement.dataset.selectedId = client.id
//  *   и скрывает dropdown.
//  */
function appendClientsToDropdownForID(clients, dropdownElement, inputElement) {
    clients.forEach(client => {
        const option = document.createElement('div');
        option.classList.add('dropdown-item');
        option.textContent = client.client_code;
        option.dataset.clientId = client.id;

        option.addEventListener('click', (event) => {
            event.stopPropagation();
            // Запишем понятное значение
            inputElement.value = client.client_code;
            // А ID клиента сохраним в dataset
            inputElement.dataset.selectedId = client.id;

            dropdownElement.style.display = 'none'; // Скрываем меню
            dropdownElement.innerHTML = '';         // Очищаем список
        });

        dropdownElement.appendChild(option);
    });
}


// Функция для подгрузки дополнительных клиентов
async function loadMoreClients(page = 2, pageSize = 7) {
    try {
        const resp = await fetch(`/cargo_acc/api/get_clients/?search=&page_size=${pageSize}&page=${page}`);
        const data = await resp.json();
        console.log("Клиенты: ", data);
        if (data.results && data.results.length > 0) {
            window.clientData = window.clientData.concat(data.results);
            console.log(`Подгружено клиентов со страницы ${page}:`, data.results);
        } else {
            console.log("Данные закончились, больше клиентов нет.");
        }
    } catch (e) {
        console.error("Ошибка подгрузки клиентов:", e);
    }
}

// Добавляем обработчик события прокрутки страницы
window.addEventListener('scroll', async () => {
    if (window.innerHeight + window.scrollY >= document.body.offsetHeight) {
        currentPage++;
        console.log(`Запрашиваем данные страницы ${currentPage}`);
        await loadMoreClients(currentPage, pageSize);
    }
});


// модалка сеттингс
async function openSettingsModal(modalId, tableName, tableId, tableData) {
    if (!document.getElementById(modalId)) {
        fetch('/cargo_acc/settings_modal')
            .then(response => response.text())
            .then(html => {
                document.body.insertAdjacentHTML('beforeend', html);
                initializeSettingsModal(modalId, tableName, tableId, tableData);
            });
    } else {
        await loadTableSettings(tableId); // Загрузка настроек
        initializeSettingsModal(modalId, tableName, tableId, tableData);
    }
}


// Онлайн применение настроек
function initializeSettingsModal(modalId, tableName, tableId, tableData) {
    const modal = document.getElementById(modalId);
    const form = modal.querySelector('#settings-form');
    const settings = tableSettings[tableData.tableId];
    form.innerHTML = ''; // Очистка формы

    const fields = tableMetadata[tableId].fields.filter(field => field.name !== 'product_code');
    fields.forEach(field => {
        const div = document.createElement('div');
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = field.name;
        checkbox.name = field.name;
        checkbox.checked = settings && field.name in settings ? settings[field.name] : true;


        checkbox.addEventListener('change', () => {
            // Обновляем настройки в tableSettings
            if (!tableSettings[tableId]) {
                tableSettings[tableId] = {};
            }
            tableSettings[tableId][field.name] = checkbox.checked;

            // Полная перегенерация таблицы
            generateTable(tableMetadata[tableId]);
        });

        const label = document.createElement('label');
        label.htmlFor = field.name;
        label.textContent = field.label;

        div.appendChild(checkbox);
        div.appendChild(label);
        form.appendChild(div);
    });
    document.getElementById('settings-close-modal').onclick = () => closeModal(modalId);
    document.getElementById('settings-cancel-modal').onclick = () => closeModal(modalId);

    modal.style.display = 'block';
    document.getElementById('save-settings').onclick = () => saveSettingsToDB(tableId);
}


// Сохранение настроек
function saveSettingsToDB(tableId) {
    const checkboxes = document.querySelectorAll('#settings-form input[type="checkbox"]');
    const settings = {};
    checkboxes.forEach(checkbox => {
        settings[checkbox.name] = checkbox.checked;
    });

    fetch('/cargo_acc/api/save_table_settings/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken()},
        body: JSON.stringify(settings)
    }).then(response => {
        if (response.ok) {
            closeModal('settings-modal'); // Просто закрываем модалку
        } else {
            console.error('Ошибка сохранения настроек.'); // Вывод ошибки в консоль
        }
    });

}


// Загрузка настроек
async function loadTableSettings(tableId) {
    try {
        const response = await fetch(`/cargo_acc/api/get_table_settings/?table_id=${tableId}`);
        if (response.ok) {
            tableSettings[tableId] = await response.json();
        } else {
            console.error('Ошибка загрузки настроек:', response.statusText);
            tableSettings[tableId] = {}; // Установить пустые настройки по умолчанию
        }
    } catch (error) {
        console.error('Ошибка загрузки настроек:', error);
        tableSettings[tableId] = {}; // Установить пустые настройки по умолчанию
    }
}
