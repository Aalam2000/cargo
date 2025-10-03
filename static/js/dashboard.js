document.addEventListener('DOMContentLoaded', function () {
    loadTableData('/cargo_acc/api/companies/', 'company-table', ['name', 'registration', 'description']);
    loadTableData('/cargo_acc/api/clients/', 'client-table', ['client_code', 'company', 'description']);
    loadTableData('/cargo_acc/api/warehouses/', 'warehouse-table', ['name', 'address', 'company']);
    loadTableData('/cargo_acc/api/products/', 'product-table', [
        'product_code', 'client_code', 'company', 'warehouse', 'cargo_type',
        'weight', 'volume', 'cost', 'shipping_date', 'delivery_date'
    ]);
    // Загрузка данных для Типов Груза
    loadTableData('/cargo_acc/api/cargo-types/', 'cargo-types-table', ['name', 'description']);

    // Загрузка данных для Статусов Груза
    loadTableData('/cargo_acc/api/cargo-statuses/', 'cargo-statuses-table', ['name', 'description']);

    // Загрузка данных для Типов Упаковок
    loadTableData('/cargo_acc/api/packaging-types/', 'packaging-types-table', ['name', 'description']);

    loadTableData('/cargo_acc/api/cargos/', 'cargo-table', [
        'cargo_code', 'client_code', 'weight', 'volume', 'cost',
        'shipping_date', 'delivery_date', 'status'
    ]);
    loadTableData('/cargo_acc/api/vehicles/', 'vehicle-table', [
        'license_plate', 'model', 'carrier_company', 'current_status'
    ]);
    loadTableData('/cargo_acc/api/transport-bills/', 'transport-bill-table', [
        'bill_code', 'departure_place', 'destination_place', 'shipping_date', 'delivery_date', 'carrier_company'
    ]);
    loadTableData('/cargo_acc/api/cargo-movements/', 'cargo-movement-table', [
        'cargo', 'from_transport_bill', 'to_transport_bill', 'movement_place', 'movement_date'
    ]);
});

function loadTableData(apiUrl, tableId, columnsMap) {
    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById(tableId).querySelector('tbody');
            tableBody.innerHTML = ''; // Очищаем тело таблицы

            data.forEach((item) => {
                const row = document.createElement('tr');
                row.classList.add('table-row');

                columnsMap.forEach((columnKey) => {
                    const cell = document.createElement('td');
                    const value = item[columnKey];
                    cell.textContent = value !== undefined && value !== null ? value : '—';
                    row.appendChild(cell);
                });

                tableBody.appendChild(row);
            });
        })
        .catch(error => console.error('Error loading table data:', error));
}


document.addEventListener('DOMContentLoaded', function () {
    const settingsButtons = document.querySelectorAll('.settings-button');
    const settingsModal = document.getElementById('settings-modal');
    const modalBackground = document.createElement('div');
    modalBackground.classList.add('modal-background');
    document.body.appendChild(modalBackground);

    settingsButtons.forEach(button => {
        button.addEventListener('click', function () {
            const tableId = button.getAttribute('data-table');
            openSettingsModal(tableId);
        });
    });

    function openSettingsModal(tableId) {
        settingsModal.style.display = 'block';
        modalBackground.style.display = 'block';
        // Центрирование модального окна
        const rect = settingsModal.getBoundingClientRect();
        settingsModal.style.top = `calc(50% - ${rect.height / 2}px)`;
        settingsModal.style.left = `calc(50% - ${rect.width / 2}px)`;

        // Закрытие модального окна при клике на фон
        modalBackground.addEventListener('click', function () {
            closeSettingsModal();
        });
    }

    function closeSettingsModal() {
        settingsModal.style.display = 'none';
        modalBackground.style.display = 'none';
    }
});
document.addEventListener('DOMContentLoaded', function () {
    const settingsButtons = document.querySelectorAll('.settings-button');
    const settingsModal = document.getElementById('settings-modal');
    const settingsList = document.getElementById('settings-list');
    const modalBackground = document.createElement('div');  // Фон
    modalBackground.classList.add('modal-background');
    document.body.appendChild(modalBackground);

    let currentColumns = [];
    let hiddenColumns = new Set();  // Скрытые колонки
    let isModalOpen = false;  // Переменная для отслеживания состояния модального окна

    // Открытие модального окна с настройками колонок
    function openSettingsModal(tableId) {
        const table = document.getElementById(tableId);
        const tableHeaders = Array.from(table.querySelectorAll('th')).map(th => th.textContent.trim());

        currentColumns = tableHeaders.slice();
        settingsList.innerHTML = '';

        // Генерация пунктов настроек для колонок
        tableHeaders.forEach((header) => {
            const li = document.createElement('li');
            li.classList.add('settings-item');
            li.setAttribute('data-column', header);

            // Перетаскивание
            const dragHandle = document.createElement('div');
            dragHandle.classList.add('drag-handle');
            dragHandle.innerHTML = '<span class="dots">::</span>';
            li.appendChild(dragHandle);

            // Чекбокс для видимости колонок
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.classList.add('column-checkbox');
            checkbox.checked = !hiddenColumns.has(header);
            checkbox.addEventListener('change', function () {
                if (this.checked) {
                    hiddenColumns.delete(header);
                } else {
                    hiddenColumns.add(header);
                }
                updateTableColumns(tableId);
            });
            li.appendChild(checkbox);

            // Название колонки
            const label = document.createElement('span');
            label.textContent = header;
            li.appendChild(label);

            settingsList.appendChild(li);
        });

        // Отображаем модальное окно и фон
        settingsModal.style.display = 'block';
        modalBackground.style.display = 'block';

        // Центрирование модального окна
        const rect = settingsModal.getBoundingClientRect();
        settingsModal.style.top = `calc(50% - ${rect.height / 2}px)`;
        settingsModal.style.left = `calc(50% - ${rect.width / 2}px)`;

        // Закрытие модального окна кликом на фон
        modalBackground.addEventListener('click', function () {
            closeSettingsModal();
        });
    }

    // Закрытие модального окна и сохранение настроек
    function closeSettingsModal() {
        settingsModal.style.display = 'none';
        modalBackground.style.display = 'none';
        saveTableSettings();
    }

    // Обновление порядка колонок в таблице
    function updateTableColumns(tableId) {
        const table = document.getElementById(tableId);
        const headerRow = table.querySelector('thead tr');
        const rows = Array.from(table.querySelectorAll('tbody tr'));

        headerRow.innerHTML = '';  // Очищаем заголовки
        currentColumns.forEach((column) => {
            const th = document.createElement('th');
            th.textContent = column;
            th.style.display = hiddenColumns.has(column) ? 'none' : '';  // Скрываем, если колонка отмечена как скрытая
            headerRow.appendChild(th);
        });

        // Обновляем содержимое строк
        rows.forEach(row => {
            const cells = Array.from(row.querySelectorAll('td'));
            const newCells = [];
            currentColumns.forEach((column, index) => {
                const cell = cells[index];
                cell.style.display = hiddenColumns.has(column) ? 'none' : '';
                newCells.push(cell);
            });
            row.innerHTML = '';
            newCells.forEach(cell => row.appendChild(cell));
        });
    }

    // Сохранение настроек таблицы на сервере
    function saveTableSettings() {
        const settingsItems = document.querySelectorAll('.settings-item');
        const settings = Array.from(settingsItems).map(item => {
            const column = item.getAttribute('data-column');
            const visible = item.querySelector('input[type="checkbox"]').checked;
            const position = Array.from(item.parentElement.children).indexOf(item);  // Порядок отображения

            return {
                name: column,
                visible: visible,
                position: position
            };
        });

        fetch('/cargo_acc/api/save_table_settings/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({columns: settings}),
        })
        .then(response => response.json())
        .then(data => {
            console.log('Настройки сохранены:', data);
        })
        .catch(error => {
            console.error('Ошибка при сохранении настроек:', error);
        });
    }

    // Открытие/закрытие модального окна при клике на шестеренку
    settingsButtons.forEach(button => {
        button.addEventListener('click', function () {
            const tableId = this.getAttribute('data-table');
            if (isModalOpen) {
                closeSettingsModal();
            } else {
                openSettingsModal(tableId);
            }
            isModalOpen = !isModalOpen;
        });
    });
});


document.addEventListener('DOMContentLoaded', function () {
    const settingsButton = document.querySelector('.settings-button');
    const settingsModal = document.getElementById('settings-modal');
    const settingsList = document.getElementById('settings-list');
    const modalBackground = document.createElement('div');  // Фон
    modalBackground.classList.add('modal-background');
    document.body.appendChild(modalBackground);  // Добавляем фон на страницу

    const tableHeaders = ['Код Клиента', 'Компания', 'Описание']; // Стандартный порядок колонок

    let currentColumns = tableHeaders.slice();  // Порядок колонок
    let hiddenColumns = new Set();  // Скрытые колонки
    let isModalOpen = false;  // Переменная для отслеживания состояния модального окна



// Открытие модального окна для настроек колонок
    function openSettingsModal() {
        const settingsButton = document.querySelector('.settings-button');
        const settingsModal = document.querySelector('.settings-modal');
        const modalBackground = document.querySelector('.modal-background');

        // Отображаем модальное окно и фон
        settingsModal.style.display = 'block';
        modalBackground.style.display = 'block';
        settingsButton.classList.add('settings-button-active');

        // Получаем размеры и позицию кнопки шестеренки
        const rect = settingsButton.getBoundingClientRect();

        // Позиционируем окно, чтобы его правый верхний угол был под левым нижним углом шестеренки
        settingsModal.style.left = `${rect.left}px`;  // Левый край модального окна совпадает с левым краем шестеренки
        settingsModal.style.top = `${rect.bottom + 10}px`;  // Модальное окно появляется чуть ниже шестеренки

        // Закрываем модальное окно кликом на фон
        modalBackground.addEventListener('click', function () {
            closeSettingsModal();
        });

        // Добавляем обработчик для повторного закрытия по клику на шестеренку
        settingsButton.addEventListener('click', function () {
            closeSettingsModal();
        });

        // Загрузка настроек пользователя при открытии
        //loadTableSettings();
    }

// Закрытие модального окна и сохранение настроек
    function closeSettingsModal() {
        const settingsModal = document.querySelector('.settings-modal');
        const modalBackground = document.querySelector('.modal-background');
        const settingsButton = document.querySelector('.settings-button');

        // Скрываем модальное окно и фон
        settingsModal.style.display = 'none';
        modalBackground.style.display = 'none';
        settingsButton.classList.remove('settings-button-active');

        // Сохраняем изменения настроек
        saveTableSettings();
    }


    // Открытие/закрытие модального окна при клике на шестеренку
    settingsButton.addEventListener('click', function () {
        if (isModalOpen) {
            applySettings();  // Применение настроек перед закрытием
        } else {
            openSettingsModal();
        }
        isModalOpen = !isModalOpen;
    });

    // Закрытие модального окна при клике на фон
    modalBackground.addEventListener('click', function (event) {
        if (event.target === modalBackground) {
            applySettings();  // Применение настроек перед закрытием
            isModalOpen = false;
        }
    });

    // Применение настроек и закрытие окна
    function applySettings() {
        closeSettingsModal();  // Закрываем модальное окно
        updateTableColumns();  // Обновляем таблицу с новым порядком колонок
        saveTableSettings();  // Сохраняем настройки таблицы для пользователя
    }

    // Обновление порядка колонок в таблице
    function updateTableColumns() {
        const table = document.getElementById('client-table'); // Измените ID таблицы для каждой нужной таблицы
        const headerRow = table.querySelector('thead tr');
        const rows = Array.from(table.querySelectorAll('tbody tr'));

        headerRow.innerHTML = '';
        currentColumns.forEach((column) => {
            const header = document.createElement('th');
            header.textContent = column;
            header.style.display = hiddenColumns.has(column) ? 'none' : '';  // Учитываем скрытые колонки
            headerRow.appendChild(header);
        });

        rows.forEach(row => {
            const cells = Array.from(row.querySelectorAll('td')); // Все ячейки строки
            const newCells = [];

            currentColumns.forEach((column, index) => {
                const cell = cells[index];
                cell.style.display = hiddenColumns.has(column) ? 'none' : '';
                newCells.push(cell);
            });

            row.innerHTML = '';
            newCells.forEach(cell => row.appendChild(cell));
        });
    }

    // Сохранение настроек на сервере
    // Сохранение настроек таблицы (порядок и видимость колонок)
    function saveTableSettings() {
        const settingsItems = document.querySelectorAll('.settings-item');
        const settings = Array.from(settingsItems).map(item => {
            const column = item.getAttribute('data-column');
            const visible = item.querySelector('input[type="checkbox"]').checked;
            const position = Array.from(item.parentElement.children).indexOf(item);  // Порядок отображения

            return {
                name: column,
                visible: visible,
                position: position
            };
        });

        fetch('/cargo_acc/api/save_table_settings/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({columns: settings}),
        })
            .then(response => response.json())
            .then(data => {
                console.log('Настройки сохранены:', data);
                applyTableSettings();  // Применяем изменения сразу к таблице
            })
            .catch(error => {
                console.error('Ошибка при сохранении настроек:', error);
            });
    }

    // Применение настроек к таблице (скрытие колонок и их порядок)
    function applyTableSettings() {
        fetch('/cargo_acc/api/get_table_settings/')
            .then(response => response.json())
            .then(data => {
                const columns = data.columns;
                const table = document.querySelector('#client-table');  // Пример для таблицы "Клиенты"

                columns.forEach(column => {
                    const th = table.querySelector(`th[data-column="${column.name}"]`);
                    const tds = table.querySelectorAll(`td[data-column="${column.name}"]`);

                    if (th) {
                        th.style.display = column.visible ? '' : 'none';
                    }

                    tds.forEach(td => {
                        td.style.display = column.visible ? '' : 'none';
                    });
                });

                // Применяем порядок колонок
                const orderedColumns = columns.sort((a, b) => a.position - b.position);
                orderedColumns.forEach((column, index) => {
                    const th = table.querySelector(`th[data-column="${column.name}"]`);
                    const tds = table.querySelectorAll(`td[data-column="${column.name}"]`);

                    if (th) {
                        th.style.order = index;
                    }

                    tds.forEach(td => {
                        td.style.order = index;
                    });
                });
            })
            .catch(error => {
                console.error('Ошибка при применении настроек:', error);
            });
    }

    // Функция для получения CSRF-токена
    function getCSRFToken() {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, 10) === 'csrftoken=') {
                    cookieValue = decodeURIComponent(cookie.substring(10));
                    break;
                }
            }
        }
        return cookieValue;
    }

   // loadTableSettings();  // Загружаем настройки при загрузке страницы
});
