// Универсальная информация о таблицах
const tableMetadata = {
    'product-table': {
        tableId: 'product-table',
        modalId: 'product-modal', // ID модального окна
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
            },
        ]
    },
    'client-table': {
        tableId: 'client-table',
        modalId: 'modal-table', // ID модального окна
        apiPath: '/cargo_acc/api/clients/',
        fields: [
            {name: 'client_code', label: 'Код клиента', type: 'CharField', visible: true},
            {name: 'company', label: 'Компания', type: 'ForeignKey', relatedModel: 'companies', visible: true},
            {name: 'description', label: 'Описание', type: 'CharField', visible: true},
        ]
    },
    'company-table': {
        tableId: 'company-table',
        modalId: 'modal-table', // ID модального окна
        apiPath: '/cargo_acc/api/companies/',
        fields: [
            {name: 'name', label: 'Название компании', type: 'CharField', visible: true},
            {name: 'registration', label: 'Регистрация', type: 'CharField', visible: true},
            {name: 'description', label: 'Описание', type: 'CharField', visible: true},
        ]
    },
    'warehouse-table': {
        tableId: 'warehouse-table',
        modalId: 'modal-table', // ID модального окна
        apiPath: '/cargo_acc/api/warehouses/',
        fields: [
            {name: 'name', label: 'Название склада', type: 'CharField', visible: true},
            {name: 'address', label: 'Адрес', type: 'CharField', visible: true},
            {name: 'company', label: 'Компания', type: 'ForeignKey', relatedModel: 'companies', visible: true},
        ]
    },
    'cargo-type-table': {
        tableId: 'cargo-type-table',
        modalId: 'modal-table', // ID модального окна
        apiPath: '/cargo_acc/api/cargo-types/',
        fields: [
            {name: 'name', label: 'Тип груза', type: 'CharField', visible: true},
            {name: 'description', label: 'Описание', type: 'CharField', visible: true},
        ]
    },
    'cargo-status-table': {
        tableId: 'cargo-status-table',
        modalId: 'modal-table', // ID модального окна
        apiPath: '/cargo_acc/api/cargo-statuses/',
        fields: [
            {name: 'name', label: 'Статус груза', type: 'CharField', visible: true},
            {name: 'description', label: 'Описание', type: 'CharField', visible: true},
        ]
    },
    'packaging-type-table': {
        tableId: 'packaging-type-table',
        modalId: 'modal-table', // ID модального окна
        apiPath: '/cargo_acc/api/packaging-types/',
        fields: [
            {name: 'name', label: 'Тип упаковки', type: 'CharField', visible: true},
            {name: 'description', label: 'Описание', type: 'CharField', visible: true},
        ]
    },
    'image-table': {
        tableId: 'image-table',
        modalId: 'image-modal', // ID модального окна
        apiPath: '/cargo_acc/api/images/',
        fields: [
            {name: 'image_file', label: 'Файл изображения', type: 'ImageField', visible: true},
            {name: 'upload_date', label: 'Дата загрузки', type: 'DateTimeField', visible: true},
        ]
    },
    'cargo-table': {
        tableId: 'cargo-table',
        modalId: 'modal-table', // ID модального окна
        apiPath: '/cargo_acc/api/cargos/',
        fields: [
            {name: 'cargo_code', label: 'Код груза', type: 'CharField', visible: true},
            {name: 'client', label: 'Клиент', type: 'ForeignKey', relatedModel: 'clients', visible: true},
            {name: 'products', label: 'Товары', type: 'ManyToManyField', relatedModel: 'products', visible: true},
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
            },
        ]
    },
    'vehicle-table': {
        tableId: 'vehicle-table',
        modalId: 'modal-table', // ID модального окна
        apiPath: '/cargo_acc/api/vehicles/',
        fields: [
            {name: 'license_plate', label: 'Номерной знак', type: 'CharField', visible: true},
            {name: 'model', label: 'Модель', type: 'CharField', visible: true},
            {
                name: 'carrier_company',
                label: 'Компания-перевозчик',
                type: 'ForeignKey',
                relatedModel: 'carrier-companies',
                visible: true
            },
            {name: 'current_status', label: 'Текущий статус', type: 'CharField'},
        ]
    },
    'transport-bill-table': {
        tableId: 'transport-bill-table',
        modalId: 'modal-table', // ID модального окна
        apiPath: '/cargo_acc/api/transport-bills/',
        fields: [
            {name: 'bill_code', label: 'Код накладной', type: 'CharField'},
            {name: 'cargos', label: 'Грузы', type: 'ManyToManyField', relatedModel: 'cargos'},
            {name: 'vehicle', label: 'Транспортное средство', type: 'ForeignKey', relatedModel: 'vehicles'},
            {name: 'departure_place', label: 'Место отправления', type: 'CharField'},
            {name: 'destination_place', label: 'Место назначения', type: 'CharField'},
            {name: 'departure_date', label: 'Дата отправления', type: 'DateField'},
            {name: 'arrival_date', label: 'Дата прибытия', type: 'DateField'},
            {
                name: 'carrier_company',
                label: 'Компания-перевозчик',
                type: 'ForeignKey',
                relatedModel: 'carrier-companies',
                visible: true
            },
        ]
    }
};


// Глобальная переменная для хранения списка компаний
let companyList = [];

// Функция для загрузки таблиц, присутствующих на странице
function loadTablesOnPage() {
    // Проходим по каждой таблице в tableMetadata
    Object.values(tableMetadata).forEach(tableData => {
        const tableElement = document.getElementById(tableData.tableId);
        if (tableElement) {
            // Извлекаем первое поле и используем его имя для сортировки
            const defaultSortField = tableData.fields[0].name;
            loadTableData(tableData, defaultSortField); // Загружаем таблицы с сортировкой по умолчанию
        }
    });
}

// Функция для загрузки данных конкретной таблицы после изменений
async function reloadTable(tableId, sortBy = 'name') {
    const tableData = tableMetadata[tableId];

    if (tableData) {
        // Проверяем, есть ли поле для сортировки в списке полей таблицы
        const validSortField = tableData.fields.find(field => field.name === sortBy);

        if (!validSortField) {
            // Если поле для сортировки не найдено, используем первое поле таблицы по умолчанию
            sortBy = tableData.fields[0].name;
            console.warn(`Поле для сортировки '${sortBy}' не найдено, используется поле по умолчанию: ${sortBy}`);
        }

        // Загружаем таблицу с найденным полем для сортировки или полем по умолчанию
        await loadTableData(tableData, sortBy);
    } else {
        console.error(`Таблица с ID ${tableId} не найдена.`);
    }
}


// Получаем CSRF-токен из cookies
function getCSRFToken() {
    const cookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
    return cookie ? decodeURIComponent(cookie.split('=')[1]) : null;
}

// Функция для инициализации перетаскивания модального окна
function enableModalDrag(modal, header) {
    let isDragging = false, offsetX, offsetY;

    // Начало перетаскивания
    header.addEventListener('mousedown', (event) => {
        event.preventDefault();  // Предотвращаем возможные побочные эффекты браузера
        isDragging = true;
        offsetX = event.clientX - modal.offsetLeft;
        offsetY = event.clientY - modal.offsetTop;

        // Привязываем обработчики событий для перетаскивания и завершения
        document.addEventListener('mousemove', moveAt);
        document.addEventListener('mouseup', stopDragging);
    });

    // Функция для перетаскивания окна
    function moveAt(event) {
        if (isDragging) {
            modal.style.left = `${event.clientX - offsetX}px`;
            modal.style.top = `${event.clientY - offsetY}px`;
        }
    }

    // Прекращение перетаскивания
    function stopDragging() {
        if (isDragging) {
            isDragging = false;
            // Удаляем привязанные события после завершения перетаскивания
            document.removeEventListener('mousemove', moveAt);
            document.removeEventListener('mouseup', stopDragging);
        }
    }
}

function generateTableHeader(tableData) {
    const thead = document.querySelector(`#${tableData.tableId} thead`);
    thead.innerHTML = ''; // Очищаем шапку перед заполнением

    const headerRow = document.createElement('tr');
    headerRow.classList.add('table-header'); // Сохраняем CSS-класс шапки

    tableData.fields
        .filter(field => field.visible) // Только видимые поля
        .forEach(field => {
            const th = document.createElement('th');
            th.textContent = field.label;
            headerRow.appendChild(th);
        });

    // Добавляем колонку для действий (например, удаление)
    const actionTh = document.createElement('th');
    actionTh.innerHTML = '<i class="fa fa-trash"></i>'; // Сохраняем иконку
    headerRow.appendChild(actionTh);

    thead.appendChild(headerRow);
}


// Функция загрузки данных в таблицу
async function loadTableData(tableData) {
    const tableBody = document.querySelector(`#${tableData.tableId} tbody`);
    tableBody.innerHTML = ''; // Очищаем существующее содержимое

    try {
        const response = await fetch(tableData.apiPath);
        const data = await response.json();

        data.forEach(item => {
            const row = document.createElement('tr');
            row.classList.add('table-row');

            tableData.fields
                .filter(field => field.visible)
                .forEach(field => {
                    const td = document.createElement('td');
                    td.textContent = item[field.name] || 'N/A';
                    row.appendChild(td);
                });

            // Добавляем колонку для удаления

            row.appendChild(actionTd);

            tableBody.appendChild(row);
        });
    } catch (error) {
        console.error('Ошибка при загрузке данных:', error);
    }
}

async function deleteRow(tableId, itemId) {
    const tableData = tableMetadata[tableId];
    try {
        const response = await fetch(`${tableData.apiPath}${itemId}/`, {
            method: 'DELETE',
            headers: {'X-CSRFToken': getCSRFToken()}
        });

        if (response.ok) {
            console.log(`Элемент с ID ${itemId} удален.`);
            loadTableData(tableData); // Обновляем таблицу после удаления
        } else {
            throw new Error('Ошибка при удалении элемента');
        }
    } catch (error) {
        console.error(error);
    }
}


function createTableRow(tableData, item) {
    //console.log('Создание строки для:', item);  // Отладка: что приходит в item

    // Генерация HTML для строки таблицы
    const rowHtml = tableData.fields.map(field => {
        const value = item[field.name];  // Получаем значение напрямую из item

        // Обработка поля с изображениями
        if (field.name === 'images') {
            return `<td class="images-cell">
                ${Array.isArray(value) && value.length > 0
                ? value.map(imageUrl =>
                    `<img src="${imageUrl}" class="image-preview" onclick="showFullSizeImage('${imageUrl}')" alt="Фото груза" />`
                ).join(' ')
                : '<button class="add-image-button" onclick="openImageModal()">Add Image</button>'
            }
            </td>`;
        }

        // Если поле — ForeignKey, выводим значение напрямую (например, строку)
        if (field.type === 'ForeignKey') {
            return `<td>${value || 'N/A'}</td>`;
        }

        // Если поле — ManyToManyField, обрабатываем как массив
        if (field.type === 'ManyToManyField' && Array.isArray(value)) {
            return `<td>${value.length > 0
                ? value.map(related => related.name).join(', ')
                : 'N/A'
            }</td>`;
        }

        // Для остальных полей просто выводим значение или 'N/A'
        return `<td>${value !== undefined && value !== null ? value : 'N/A'}</td>`;
    }).join('');  // Объединяем все ячейки в одну строку

    // Генерируем итоговую строку таблицы
    return `<tr class="table-row" data-item-id="${item.id}" onclick="openModal(tableMetadata['${tableData.tableId}'], ${item.id})">
                ${rowHtml}
                <td>
                    <img src="/web/staticlete-icon.png" class="delete-icon" 
                         onclick="event.stopPropagation(); openDeleteConfirmationModal('${tableData.tableId}', ${item.id}, item)">
                </td>
            </tr>`;
}


// Функция для загрузки изображения в таблицу "images" и привязки к текущей записи продукта
function openImageUploadForProductTable(productId) {
    // Открываем модальное окно для загрузки изображения
    const imageModal = document.getElementById('image-modal');
    const fileInput = document.getElementById('image-file');
    const imagePreview = document.getElementById('image-preview');

    // Очищаем поле ввода и превью
    fileInput.value = '';
    imagePreview.src = '';
    imagePreview.style.display = 'none';

    // Показать модальное окно
    imageModal.style.display = 'flex';

    // Добавляем обработчик события для формы загрузки
    document.getElementById('image-upload-form').addEventListener('submit', function (event) {
        event.preventDefault();
        const productId = document.getElementById('product-id').value; // ID продукта
        const formData = new FormData();
        const fileInput = document.getElementById('image-file');

        if (fileInput.files.length > 0) {
            formData.append('image_file', fileInput.files[0]);
        }

        fetch(`/cargo_acc/products/${productId}/add-image/`, {
            method: 'POST', body: formData, headers: {
                'X-CSRFToken': getCSRFToken(), // CSRF защита
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Обновляем поле с изображениями в таблице товаров
                    const imagesCell = document.querySelector(`#product-${productId} .images-cell`);
                    imagesCell.innerHTML += `<img src="${data.image_url}" class="image-preview" onclick="showFullSizeImage('${data.image_url}')">`;

                    // Закрываем модальное окно после успешной загрузки
                    toggleModal('image-modal', false);
                } else {
                    console.error('Ошибка при добавлении изображения:', data.message);
                }
            })
            .catch(error => {
                console.error('Ошибка при загрузке изображения:', error);
            });
    });

}

// Функция открытия модального окна подтверждения удаления
function openDeleteConfirmationModal(tableId, itemId, itemData) {
    const modalDel = document.getElementById('delete-confirmation-modal');
    const message = document.getElementById('delete-confirmation-message');

    // Определяем основное текстовое поле для сообщения удаления на основе метаданных таблицы
    const tableData = tableMetadata[tableId];
    const displayField = tableData.fields.find(field => field.type === 'CharField' || field.type === 'TextField') || tableData.fields[0]; // Используем текстовое поле или первое поле по умолчанию

    // Генерируем сообщение с указанием основного поля
    message.textContent = `Вы действительно хотите удалить элемент '${itemData[displayField.name]}' с ID: ${itemId}?`;

    const confirmButton = document.getElementById('confirm-delete');
    confirmButton.onclick = async () => {
        await deleteTableRow(tableData, itemId); // Передаем метаданные таблицы и ID для удаления
        toggleModal('delete-confirmation-modal', false); // Закрываем модальное окно после удаления
    };

    // Получаем кнопку отмены для окна подтверждения удаления
    const cancelDeleteButton = document.getElementById('cancel-delete');
    if (cancelDeleteButton) {
        cancelDeleteButton.onclick = () => toggleModal('delete-confirmation-modal', false); // Закрытие окна при отмене
    }

    toggleModal('delete-confirmation-modal', true); // Показываем модальное окно
}


// Универсальная функция удаления строки из таблицы
async function deleteTableRow(tableData, itemId) {
    try {
        // Выполняем запрос DELETE для удаления элемента
        const response = await fetch(`${tableData.apiPath}${itemId}/`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
            },
        });

        // Проверяем успешность запроса
        if (!response.ok) {
            throw new Error('Ошибка при удалении элемента');
        }

        // Обновляем только изменённую таблицу после успешного удаления
        await reloadTable(tableData.tableId);

        // Отображаем сообщение об успешном удалении (опционально)
        console.log(`Элемент с ID ${itemId} был успешно удалён из таблицы ${tableData.tableId}.`);

    } catch (error) {
        // Выводим ошибку в консоль и отображаем сообщение пользователю
        console.error(`Ошибка при удалении элемента с ID ${itemId}:`, error);
        alert('Произошла ошибка при удалении элемента. Попробуйте снова.');
    }
}


// Универсальная функция для открытия модального окна редактирования или добавления новой строки
async function openModal(tableData, modalId, itemId = null, mode = 'create') {
    //console.log('tableData: ' + tableData, 'modalId: ' + modalId, 'itemId: ' + itemId, 'mode: ' + mode)
    const modal = document.getElementById(modalId); // Получаем нужное модальное окно
    if (!modal) {
        console.error(`Модальное окно с ID '${modalId}' не найдено.`);
        return;
    }

    const modalForm = modal.querySelector('#modal-form');
    if (!modalForm) {
        console.error('Элемент с ID "modal-form" не найден в модальном окне.');
        return;
    }

    modalForm.innerHTML = ''; // Очищаем форму перед заполнением

    let item = null;
    if (mode === 'edit' && itemId) {
        try {
            const response = await fetch(`${tableData.apiPath}${itemId}/`);
            if (!response.ok) throw new Error('Ошибка при загрузке данных');
            item = await response.json();
        } catch (error) {
            console.error('Ошибка при загрузке данных:', error);
            alert('Произошла ошибка при загрузке данных.');
            return;
        }
    }

    // Заполняем поля формы
    tableData.fields.forEach(field => {
        const value = item ? item[field.name] : ''; // Либо значение, либо пустая строка
        const inputField = createInputField(field, value);
        modalForm.appendChild(inputField);
    });

    // Показываем модальное окно
    toggleModal(modalId, true);
}


// Функция для сохранения отредактированных данных
async function saveEditedData(tableData, itemId, jsonData) {
    try {
        const response = await fetch(`${tableData.apiPath}${itemId}/`, {
            method: 'PUT', // Используем метод PUT для обновления данных
            headers: {
                'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() // Передаем CSRF токен
            }, body: JSON.stringify(jsonData) // Передаем данные в формате JSON
        });

        if (!response.ok) {
            throw new Error('Ошибка при сохранении изменений');
        }

        const data = await response.json();
        toggleModal('modal-table', false); // Закрываем модальное окно при успешном обновлении
        reloadTable(tableData.tableId);  // Обновляем данные таблицы после редактирования
    } catch (error) {
        console.error('Ошибка при сохранении изменений:', error);
    }
}

// Функция для проверки уникальности поля УНИВЕРСАЛЬНАЯ
async function checkFieldUnique(inputElement, apiPath, queryParam) {
    const value = inputElement.value.trim();
    inputElement.classList.toggle('empty-field', value === '');
    inputElement.classList.remove('unique-valid', 'unique-invalid');

    if (!value) {
        inputElement.classList.add('unique-invalid');
        return;
    }

    try {
        const response = await fetch(`${apiPath}?${queryParam}=${encodeURIComponent(value)}`);
        if (!response.ok) throw new Error('Ошибка при проверке уникальности');
        const data = await response.json();
        inputElement.classList.add(data.is_unique ? 'unique-valid' : 'unique-invalid');
    } catch (error) {
        console.error('Ошибка при проверке уникальности:', error);
        inputElement.classList.add('unique-invalid');
    }
}

// Функция для сохранения нового клиента
// Функция для сохранения нового клиента
async function saveNewClient(tableData, jsonData) {
    try {
        const companyNameElement = document.getElementById('company'); // Проверяем поле имени компании
        if (companyNameElement) {
            jsonData.company = companyNameElement.value; // Добавляем имя компании в данные, если элемент существует
        } else {
            console.error('Элемент с именем компании не найден');
        }

        const response = await fetch(tableData.apiPath, {
            method: 'POST', headers: {
                'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() // Передаем CSRF токен
            }, body: JSON.stringify(jsonData) // Передаем данные в формате JSON
        });

        if (!response.ok) {
            const errorText = await response.text(); // Получение текста ошибки для отладки
            console.error('Ошибка при добавлении клиента:', errorText);
            throw new Error('Ошибка при добавлении клиента');
        }

        const data = await response.json();
        toggleModal('modal-table', false); // Закрываем модальное окно при успешном добавлении
        reloadTable(tableData.tableId); // Обновляем данные таблицы после добавления нового клиента
    } catch (error) {
        console.error('Ошибка при сохранении клиента:', error);
    }
}

// Дополнительные вспомогательные функции
function createInputField(field, value = '') {
    const container = document.createElement('div');
    container.classList.add('input-field');

    const label = document.createElement('label');
    label.setAttribute('for', field.name);
    label.textContent = field.label;

    let input;

    if (field.type === 'ForeignKey' || field.type === 'ManyToManyField') {
        input = document.createElement('select');
        input.id = field.name;
        input.name = field.name;

        // Загружаем связанные данные для поля
        fetch(`/cargo_acc/api/${field.relatedModel}/`)
            .then(response => response.json())
            .then(data => {
                data.forEach(optionData => {
                    const option = document.createElement('option');
                    option.value = optionData.id;
                    // Попытка взять поле 'name', иначе взять первое текстовое поле
                    // Попытка взять поле 'name', иначе взять альтернативное
                    option.text = optionData.name ||
                        optionData.client_code ||
                        optionData.title ||
                        optionData.company_name ||
                        'N/A';
                    if (value && value === optionData.id) {
                        option.selected = true;
                    }
                    input.appendChild(option);
                });
            })
            .catch(error => console.error('Ошибка при загрузке связанных данных:', error));
    } else {
        input = document.createElement('input');
        input.type = 'text';
        input.id = field.name;
        input.name = field.name;
        input.value = value;
    }

    container.appendChild(label);
    container.appendChild(input);
    return container;
}


function createCompanyField(value = '') {
    return `<label for="company">Компания</label>
            <input type="text" id="company" name="company" class="modal-input" value="${value}" autocomplete="off">
            <div id="company-list" class="company-list"></div>`;
}

// Обновленная функция фильтрации и выбора компании
function filterCompanies() {
    const input = document.getElementById('company').value.toLowerCase();
    const companyListDiv = document.getElementById('company-list');
    companyListDiv.innerHTML = '';

    const filteredCompanies = companyList.filter(company => company.name.toLowerCase().includes(input));
    filteredCompanies.forEach(company => {
        const option = document.createElement('div');
        option.textContent = company.name;
        option.classList.add('company-option');
        option.onclick = () => {
            document.getElementById('company').value = company.name; // Устанавливаем имя компании в поле
            companyListDiv.innerHTML = '';
        };

        companyListDiv.appendChild(option);
    });
}


// Функция загрузки и фильтрации списка компаний
async function loadFilteredCompanyList(filterText = '') {
    try {
        const response = await fetch('/cargo_acc/api/companies/');
        const companies = await response.json();

        const companyListContainer = document.getElementById('company-list');
        if (!companyListContainer) {
            console.error('Элемент company-list не найден в DOM.');
            return;
        }

        companyListContainer.innerHTML = ''; // Очищаем список перед заполнением

        const filteredCompanies = companies.filter(company => company.name.toLowerCase().includes(filterText.toLowerCase()));

        filteredCompanies.forEach(company => {
            const listItem = document.createElement('div');
            listItem.className = 'company-list-item';
            listItem.textContent = company.name;
            listItem.onclick = () => {
                document.getElementById('company').value = company.name;
                document.getElementById('company_id').value = company.id; // Заполняем поле ID компании
                companyListContainer.innerHTML = ''; // Закрываем список после выбора компании
            };
            companyListContainer.appendChild(listItem);
        });

        // Отображаем список рядом с полем "Компания"
        companyListContainer.style.width = document.getElementById('company').offsetWidth + 'px';
    } catch (error) {
        console.error('Ошибка загрузки списка компаний:', error);
    }
}

// Привязка обработчиков для поля компании
function attachCompanyFieldHandlers() {
    const companyInput = document.getElementById('company');
    if (companyInput) {
        companyInput.addEventListener('focus', () => updateCompanyList()); // Загружаем список всех компаний при фокусе
        companyInput.addEventListener('input', (event) => updateCompanyList(event.target.value)); // Фильтрация списка компаний при вводе
        document.addEventListener('click', (event) => {
            const companyListContainer = document.getElementById('company-list');
            if (companyListContainer && !companyListContainer.contains(event.target) && event.target !== companyInput) {
                companyListContainer.innerHTML = ''; // Закрываем список при клике вне его
            }
        });
    }
}


// Загрузка списка компаний при загрузке страницы
async function loadCompanyList() {
    try {
        const response = await fetch('/cargo_acc/api/companies/');
        companyList = await response.json();

        updateCompanyList(); // Обновляем список компаний в зависимости от ввода
    } catch (error) {
        console.error('Ошибка загрузки списка компаний:', error);
    }
}

function updateCompanyList(filterText = '') {
    const companyListContainer = document.getElementById('company-list');
    if (!companyListContainer) {
        console.error('Элемент company-list не найден в DOM.');
        return;
    }

    companyListContainer.innerHTML = ''; // Очищаем список перед заполнением
    const filteredCompanies = companyList.filter(company => company.name.toLowerCase().includes(filterText.toLowerCase()));

    filteredCompanies.forEach(company => {
        const listItem = document.createElement('div');
        listItem.className = 'company-list-item';
        listItem.textContent = company.name;
        listItem.onclick = () => {
            document.getElementById('company').value = company.name;
            companyListContainer.innerHTML = ''; // Закрываем список после выбора компании
        };
        companyListContainer.appendChild(listItem);
    });

    // Отображаем список рядом с полем "Компания"
    companyListContainer.style.width = document.getElementById('company').offsetWidth + 'px';
}

////////////////////////////////////////////////////////////////
document.addEventListener('DOMContentLoaded', async () => {
    const cancelButton = document.getElementById('modal-cancel');
    const deleteModal = document.getElementById('delete-confirmation-modal');
    const closeImageModal = document.getElementById('close-image-modal');
    const imageModal = document.getElementById('image-modal');
    const imageUploadForm = document.getElementById('image-upload-form');

    // Обработчик для кнопок закрытия модальных окон
    document.body.addEventListener('click', (event) => {
        const closeButton = event.target.closest('.modal-close');
        if (closeButton) {
            const modalId = closeButton.getAttribute('data-close-modal');
            toggleModal(modalId, false); // Закрываем модальное окно
        }
    });

    // Обработчик для закрытия модальных окон при клике вне их содержимого
    document.body.addEventListener('click', (event) => {
        const openModal = Array.from(document.querySelectorAll('.modal'))
            .find(modal => window.getComputedStyle(modal).display !== 'none');
        if (openModal && !openModal.contains(event.target)) {
            const modalId = openModal.closest('.modal').id;
            toggleModal(modalId, false); // Закрываем окно
        }
    });

    // Генерация заголовков и загрузка данных
    Object.values(tableMetadata).forEach(tableData => {
        const table = document.getElementById(tableData.tableId);
        if (table) {
            generateTableHeader(tableData); // Генерируем шапку таблицы
            loadTableData(tableData); // Загружаем данные таблицы
        }
    });

    // Загрузка данных только для таблицы клиентов с пагинацией
    const clientTableData = tableMetadata['client-table'];
    if (clientTableData) {
        console.log(clientTableData); // Проверка данных
        await loadTableDataWithPagination(clientTableData); // Ожидаем выполнения
    }

    // Универсальное делегирование для открытия модальных окон
    document.body.addEventListener('click', (event) => {
        const target = event.target.closest('.add-button, .table-row, .delete-button');

        if (target) {
            const tableId = target.closest('table')?.id || target.getAttribute('data-table');
            const modalId = target.getAttribute('data-modal');
            const mode = target.getAttribute('data-mode'); // create/edit/delete
            const itemId = target.getAttribute('data-item-id') || null; // ID записи

            const tableData = Object.values(tableMetadata).find(
                table => table.tableId === tableId
            );

            if (tableData) {
                openModal(tableData, modalId, itemId, mode); // Передаём все данные в функцию
            } else {
                console.error(`Метаданные для таблицы с ID '${tableId}' не найдены.`);
            }
        }

    });

    // Если форма загрузки изображения существует, привязываем обработчик
    if (imageUploadForm) {
        imageUploadForm.addEventListener('submit', function (event) {
            event.preventDefault();
            event.stopPropagation();

            const formData = new FormData();
            const fileInput = document.getElementById('image-file');

            if (fileInput.files.length > 0) {
                formData.append('image_file', fileInput.files[0]);
            }

            fetch('/cargo_acc/api/images/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCSRFToken(),
                },
            })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Ошибка при загрузке изображения');
                    }
                    return response.json();
                })
                .then(data => {
                    const notification = document.createElement('div');
                    notification.className = 'upload-notification';
                    notification.innerText = 'Изображение успешно загружено!';
                    document.body.appendChild(notification);

                    setTimeout(() => {
                        notification.remove();
                    }, 3000);

                    imageModal.style.display = 'none';
                    loadTableData(tableMetadata['image-table']); // Перезагружаем таблицу изображений
                })
                .catch(error => console.error('Ошибка при загрузке изображения:', error));
        });

        // Превью изображения при изменении выбранного файла
        document.getElementById('image-file').addEventListener('change', previewImage);
    }

    // Загружаем таблицы, присутствующие на странице
    //loadTablesOnPage();

    // Привязываем обработчики для поля компании
    //attachCompanyFieldHandlers();
    //loadCompanyList();
});

// Функция для открытия/закрытия модальных окон
function toggleModal(modalId, show = true) {
    const modal = document.getElementById(modalId);

    if (modal) {
        modal.style.display = show ? 'block' : 'none'; // Показать или скрыть модальное окно
    } else {
        console.error(`Модальное окно с ID '${modalId}' не найдено.`);
    }
}


// Превьюха картинки
function previewImage(event) {
    const reader = new FileReader();
    const imagePreview = document.getElementById('image-preview');

    reader.onload = function () {
        imagePreview.src = reader.result;
        imagePreview.style.display = 'block';

        // Добавляем обработчик клика для открытия изображения на полный экран
        imagePreview.onclick = function () {
            showFullSizeImage(imagePreview.src);  // Корректная привязка обработчика клика
        };
    };

    if (event.target.files[0]) {
        reader.readAsDataURL(event.target.files[0]);
    }
}


function openImageModal(imageId = null) {
    event.stopPropagation();  // Останавливаем всплытие события
    const imageModal = document.getElementById('image-modal');
    const fileInput = document.getElementById('image-file');
    const imagePreview = document.getElementById('image-preview');

    // Очистка поля ввода файла и превью изображения
    fileInput.value = '';
    imagePreview.src = '';
    imagePreview.style.display = 'none';

    if (imageId) {
        // Логика загрузки существующего изображения
        fetch(`/cargo_acc/api/images/${imageId}/`)
            .then(response => response.json())
            .then(data => {
                document.getElementById('file-name-display').textContent = data.image_file.split('/').pop();
                imagePreview.src = data.image_file;
                imagePreview.style.display = 'block';

                // Привязываем обработчик клика для открытия полноразмерного изображения
                imagePreview.onclick = function () {
                    showFullSizeImage(imagePreview.src);
                };
            })
            .catch(error => console.error('Ошибка при загрузке изображения:', error));
    }

    // Показ модального окна
    imageModal.style.display = 'block';
}


// Функция для отображения полноразмерного изображения
function showFullSizeImage(imageUrl) {
    const fullImageModal = document.createElement('div');
    fullImageModal.classList.add('full-image-modal');

    const fullImageContent = `
        <div class="full-image-content">
            <span class="close" id="close-full-image-modal">&times;</span>
            <img src="${imageUrl}" alt="Полноразмерное изображение" class="full-size-image">
        </div>
    `;

    fullImageModal.innerHTML = fullImageContent;
    document.body.appendChild(fullImageModal);

    // Обработчик закрытия модального окна с полноразмерным изображением
    document.getElementById('close-full-image-modal').onclick = () => {
        fullImageModal.remove();
    };
}

const PAGE_SIZE = 15; // Количество записей на страницу

async function loadTableDataWithPagination(tableData, page = 1) {
    const tableBody = document.querySelector(`#${tableData.tableId} tbody`);
    tableBody.innerHTML = ''; // Очищаем содержимое перед загрузкой

    console.log(`Загружаем данные для: ${tableData.apiPath}, страница: ${page}`); // Проверка запроса

    try {
        const response = await fetch(`${tableData.apiPath}?page=${page}&size=15`);
        if (!response.ok) {
            throw new Error(`Ошибка HTTP: ${response.status}`);
        }
        const data = await response.json();

        console.log('Полученные данные:', data); // Проверка данных

        const fragment = document.createDocumentFragment();
        data.results.forEach(item => {
            const row = document.createElement('tr');
            row.classList.add('table-row');

            tableData.fields.filter(f => f.visible).forEach(field => {
                const td = document.createElement('td');
                td.textContent = item[field.name] || 'N/A';
                row.appendChild(td);
            });

            fragment.appendChild(row);
        });

        tableBody.appendChild(fragment); // Вставляем строки в таблицу
        renderPagination(tableData, data.totalPages, page); // Отображаем пагинацию
    } catch (error) {
        console.error('Ошибка при загрузке данных:', error);
    }
}


function renderPagination(tableData, totalPages, currentPage) {
    const pagination = document.getElementById(`pagination-${tableData.tableId}`);
    pagination.innerHTML = ''; // Очищаем пагинацию

    for (let i = 1; i <= totalPages; i++) {
        const pageButton = document.createElement('button');
        pageButton.textContent = i;
        pageButton.disabled = i === currentPage;
        pageButton.onclick = () => loadTableDataWithPagination(tableData, i);
        pagination.appendChild(pageButton);
    }
}
