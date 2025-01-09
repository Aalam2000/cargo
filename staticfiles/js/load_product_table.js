// tiket: Подключение необходимых метаданных таблицы
const tableMetadata = {
    'product-table': {
        tableId: 'product-table',
        tableName: 'Таблица товаров',
        apiPath: '/cargo_acc/api/products/',
        apiDelPath: '/cargo_acc/api/delete/Product/',
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


let currentPage = 1;
const pageSize = 20;

// tiket: Функция для генерации таблицы
// Функция для генерации таблицы
async function generateTable(tableData) {
    const table = document.querySelector(`#${tableData.tableId}`);
    if (!table) {
        console.error(`Таблица с ID "${tableData.tableId}" не найдена.`);
        return;
    }

    const thead = table.querySelector('thead');
    const tbody = table.querySelector('tbody');

    // Генерация заголовков
    thead.innerHTML = '';
    const headerRow = document.createElement('tr');
    [...tableData.fields, {name: 'delete', label: '<i class="fa fa-trash"></i>'}].forEach(field => {
        const th = document.createElement('th');
        th.innerHTML = field.label;
        // Применяем класс delete-cell для последнего столбца
        if (field.name === 'delete') {
            th.classList.add('delete-cell');
        }
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);

    try {
        const response = await fetch(`${tableData.apiPath}?page=1&page_size=${pageSize}`);
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);

        const data = await response.json();
        const fragment = document.createDocumentFragment();

        data.forEach(item => {
            const row = document.createElement('tr');
            row.setAttribute('data-id', item.id);

            tableData.fields.forEach(field => {
                const td = document.createElement('td');
                td.textContent = item[field.name] || 'N/A';
                row.appendChild(td);
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
    // Прочитать значение атрибута id
    const tableId = tableElement.id;

    // Получить метаданные таблицы, используя ID
    const metadata = tableMetadata[tableId];

    if (metadata) {

        // Передать метаданные в функцию generateTable для каждой таблицы
        generateTable(metadata);
    } else {
        console.error(`Метаданные для таблицы с ID "${tableId}" не найдены.`);
    }
});


// Слушатель на клики в таблицах
document.addEventListener('click', (event) => {
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
        console.log("SETings!");
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

async function deleteRow(tableId, itemId) {
    const tableData = tableMetadata[tableId];

    if (!tableData) {
        console.error(`Метаданные для таблицы с ID "${tableId}" не найдены.`);
        return;
    }

    const tablePath = tableMetadata[tableId].apiDelPath; // Используем ваш API путь

    try {
        const response = await fetch(`${tablePath}${itemId}/`, {
            method: 'DELETE', headers: {'X-CSRFToken': getCSRFToken()}
        });

        if (response.ok) {
            // Находим строку в таблице по ID и удаляем её из DOM
            const table = document.getElementById(tableData.tableId);
            const row = table.querySelector(`[data-id="${itemId}"]`);

            if (row) {
                row.remove(); // Удаляем строку из DOM
            } else {
                console.warn(`Строка с ID ${itemId} не найдена в таблице.`);
            }
        } else {
            throw new Error('Ошибка при удалении элемента');
        }
    } catch (error) {
        console.error(error);
    }
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


async function showAddRowModal(modalId, tableName, tableId, rowInfo = null) {
    const modal = document.getElementById(modalId);
    const tableData = tableMetadata[tableId]; // Получаем метаданные таблицы

    if (!tableData) {
        console.error(`Метаданные для таблицы ${tableId} не найдены.`);
        return;
    }

    const isEditMode = rowInfo !== null;

    // Заголовок модального окна
    document.getElementById('product-modal-title').textContent = isEditMode ? 'Изменение строки' : 'Добавление строки';

    // Очистка содержимого модального окна
    const modalBody = document.getElementById('product-modal-body');
    modalBody.innerHTML = '';

    const form = document.createElement('form');
    form.id = 'add-row-form';

    const row = document.createElement('div');
    row.classList.add('d-flex', 'justify-content-between', 'align-items-start', 'gap-3');

    const fieldsToDisplay = ['product_code', 'client']; // Показываем только первые два поля

    // Загрузка клиентов перед обработкой полей
    if (fieldsToDisplay.includes('client')) {
        await loadClients();
    }

    tableData.fields.forEach((field, index) => {
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

        if (isEditMode && rowInfo.data[index] !== undefined) {
            input.value = rowInfo.data[index] !== 'N/A' ? rowInfo.data[index] : '';
        }

        // Подключаем выпадающий список для клиента
        if (field.name === 'client') {
            const dropdown = document.createElement('div');
            dropdown.classList.add('dropdown-menu');
            dropdown.style.display = 'none';
            modalBody.appendChild(dropdown);

            // Подключаем автозаполнение
            input.addEventListener('input', (event) => {
                updateClientDropdown(input, dropdown);
            });
            input.addEventListener('focus', () => {
                updateClientDropdown(input, dropdown);
            });
            input.addEventListener('blur', () => setTimeout(() => dropdown.style.display = 'none', 100));

            document.addEventListener('click', (event) => {
                if (!event.target.closest('.form-control') && !event.target.closest('.dropdown-menu')) {
                    dropdown.style.display = 'none';
                }
            });
        } else {
            // Логирование для остальных полей
            input.addEventListener('focus', () => {
                // console.log(`Activated field1: ${field.name}`);
            });
            input.addEventListener('input', (event) => {
                // console.log(`Input for field1 ${field.name}: ${event.target.value}`);
            });
        }

        formGroup.appendChild(input);
        row.appendChild(formGroup);
    });

    form.appendChild(row);
    modalBody.appendChild(form);

    // Отображение модального окна
    modal.style.display = 'block';
    document.body.classList.add('modal-open');

    // Подключение кнопок (Закрыть, Отмена, Сохранить)
    if (!modal.dataset.listenersAdded) {
        document.getElementById('product-close-modal').addEventListener('click', () => closeModal(modalId));
        document.getElementById('product-cancel-modal').addEventListener('click', () => closeModal(modalId));
        document.getElementById('product-modal-save').addEventListener('click', () => {
            console.log(isEditMode ? 'Редактирование завершено' : 'Добавление завершено');
            closeModal(modalId);
        });
        modal.dataset.listenersAdded = 'true';
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

// Функция для загрузки клиентов с сервера
// Хранилище для данных клиентов
let clientData = []; // Глобальный массив для кэширования клиентов
let clientDataLoaded = false; // Флаг, чтобы загрузка происходила один раз

// Загрузка данных клиентов с сервера (только один раз)
async function loadClients() {
    if (clientDataLoaded) return clientData; // Если уже загружено, возвращаем кэш
    try {
        const response = await fetch('/cargo_acc/api/clients/');
        if (!response.ok) throw new Error(`Ошибка загрузки клиентов: ${response.status}`);
        clientData = await response.json(); // Сохраняем данные в кэш
        clientDataLoaded = true; // Устанавливаем флаг, что данные загружены
        return clientData;
    } catch (error) {
        console.error('Ошибка загрузки клиентов:', error);
        return []; // Возвращаем пустой массив в случае ошибки
    }
}

// Фильтрация клиентов по введённому тексту
function filterClients(query) {
    return clientData
        .filter(client =>
            client.client_code.toLowerCase().includes(query.toLowerCase())
        )
        .slice(0, 7); // Возвращаем максимум 7 результатов
}

// Обновление выпадающего списка
function updateClientDropdown(inputElement, dropdownElement) {
    const query = inputElement.value.trim(); // Текущий ввод пользователя
    const filteredClients = filterClients(query); // Фильтруем данные
    const modalBody = document.getElementById('product-modal-body');

    // Очищаем старые результаты
    dropdownElement.innerHTML = '';

    if (filteredClients.length === 0) {
        dropdownElement.style.display = 'none';
        return;
    }
    // Устанавливаем позицию и ширину выпадающего окна относительно поля
    // Получаем координаты input относительно окна просмотра и модального окна
    const inputRect = inputElement.getBoundingClientRect();
    const modalRect = modalBody.getBoundingClientRect();

    // Позиционируем dropdown относительно модального окна
    modalBody.style.position = 'relative'; // чтобы отсчёт шёл от modalBody
    dropdownElement.style.position = 'absolute';
    dropdownElement.style.top = `${inputElement.offsetTop + inputElement.offsetHeight}px`;
    dropdownElement.style.left = `${inputElement.offsetLeft}px`;
    dropdownElement.style.width = `${inputElement.offsetWidth}px`;
    dropdownElement.style.zIndex = '1050';


    // Добавляем клиентов в список
    filteredClients.forEach(client => {
        const option = document.createElement('div');
        option.classList.add('dropdown-item'); // Присваиваем класс
        option.textContent = `${client.client_code} (${client.company})`; // Текст строки
        option.dataset.clientId = client.id; // Сохраняем ID клиента

        // Обработчик клика по строке
        option.addEventListener('click', (event) => {
            event.stopPropagation();
            inputElement.value = client.client_code; // Устанавливаем значение в поле
            dropdownElement.style.display = 'none'; // Скрываем меню
            dropdownElement.innerHTML = ''; // Очищаем список
        });
        // Добавляем элемент в DOM
        dropdownElement.appendChild(option);
    });
    // Показываем список
    dropdownElement.style.display = 'block';
}

