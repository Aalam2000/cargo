document.addEventListener('DOMContentLoaded', function () {
    // Основные переменные
    const saveClientBtn = document.getElementById('save-client-btn');
    const clientCodeInput = document.getElementById('clientCode');
    const clientCommentInput = document.getElementById('clientComment');
    const clientCompanyInput = document.getElementById('clientCompany');
    const clientCodeError = document.getElementById('clientCodeError');
    const modal = document.getElementById('universalModal');
    const closeModalBtn = document.getElementById('closeModal');
    const tableHeaders = document.querySelectorAll('th');

    const clientsTableHeaders = document.querySelectorAll('#clientCodeHeader, #companyHeader');
    const productsTableHeaders = document.querySelectorAll('#productCodeHeader, #productClientHeader, #productNameHeader');

    function initializeTableSort(headers, tableBodyId, defaultSortIndex) {
        if (!headers || headers.length === 0) {
            console.error(`Ошибка: Заголовки для таблицы с ID ${tableBodyId} не найдены.`);
            return;
        }

        headers.forEach((header, index) => {
            header.classList.add('sortable');

            header.addEventListener('click', function () {
                const currentSort = this.getAttribute('data-sort') || 'none';
                const isAscending = currentSort === 'asc';

                headers.forEach(h => h.removeAttribute('data-sort'));

                this.setAttribute('data-sort', isAscending ? 'desc' : 'asc');

                headers.forEach(h => {
                    const arrow = h.querySelector('.sort-arrow');
                    if (arrow) {
                        arrow.innerText = h === header ? (isAscending ? '▲' : '▼') : '⇅';
                    }
                });

                sortTable(tableBodyId, index, !isAscending);
            });
        });

        sortTable(tableBodyId, defaultSortIndex, true);
        headers[defaultSortIndex].setAttribute('data-sort', 'asc');
        const arrow = headers[defaultSortIndex].querySelector('.sort-arrow');
        if (arrow) {
            arrow.innerText = '▲';
        }
    }

    function sortTable(tableBodyId, columnIndex, isAscending) {
        const tableBody = document.getElementById(tableBodyId);
        if (!tableBody) {
            console.error(`Ошибка: Таблица с ID ${tableBodyId} не найдена.`);
            return;
        }
        const rows = Array.from(tableBody.rows);

        rows.sort((rowA, rowB) => {
            const cellA = rowA.cells[columnIndex].innerText.toLowerCase();
            const cellB = rowB.cells[columnIndex].innerText.toLowerCase();
            return isAscending ? cellA.localeCompare(cellB) : cellB.localeCompare(cellA);
        });

        rows.forEach(row => tableBody.appendChild(row));
    }

    // Инициализация сортировки для таблиц
    if (clientsTableHeaders.length > 0) {
        initializeTableSort(clientsTableHeaders, 'clientsTableBody', 0);
    }

    if (productsTableHeaders.length > 0) {
        initializeTableSort(productsTableHeaders, 'productsTableBody', 0);
    }

// Функция для обновления стрелок сортировки
    function updateSortArrows(headers, activeHeader, isAscending) {
        headers.forEach(h => {
            const arrow = h.querySelector('.sort-arrow');
            if (arrow) {
                if (h === activeHeader) {
                    arrow.innerText = isAscending ? '▼' : '▲'; // Обновляем стрелку для активной колонки
                } else {
                    arrow.innerText = '⇅'; // Двунаправленная стрелка для неактивных колонок
                }
            }
        });
    }

// Добавляем обработчик для таблицы "Товары"
    if (productsTableHeaders && productsTableHeaders.length > 0) {  // Проверка на наличие заголовков
        productsTableHeaders.forEach((header, index) => {
            header.addEventListener('click', function () {
                const currentSort = header.getAttribute('data-sort') || 'none';
                const isAscending = currentSort === 'asc';

                // Сбрасываем сортировку для всех колонок
                productsTableHeaders.forEach(h => h.removeAttribute('data-sort'));

                // Устанавливаем атрибут сортировки для текущей колонки
                header.setAttribute('data-sort', isAscending ? 'desc' : 'asc');

                // Обновляем стрелки сортировки
                updateSortArrows(productsTableHeaders, header, !isAscending);

                // Сортируем таблицу
                sortTable('productsTableBody', index, !isAscending);
            });
        });
    } else {
        console.error("Ошибка: Заголовки для таблицы 'Товары' не найдены или недоступны.");
    }


// Применяем сортировку для всех таблиц по умолчанию

    initializeTableSort(productsTableHeaders, 'productsTableBody', 0); // Сортировка по первой колонке

// Функция открытия модального окна для добавления или редактирования клиента
    function openModal(clientCode = '', clientComment = '', clientCompany = '', clientId = null) {
        clientCodeInput.value = clientCode;
        clientCommentInput.value = clientComment;
        clientCompanyInput.value = clientCompany;
        modal.setAttribute('data-client-id', clientId || '');
        modal.style.display = 'block';

        // Устанавливаем состояние поля "Код Клиента"
        if (!clientCode) {
            clientCodeInput.classList.add('error');
            clientCodeInput.style.border = '2px solid red';
            clientCodeError.textContent = 'Обязательно заполнить';
            clientCodeError.style.display = 'block';
        } else {
            clientCodeInput.classList.remove('error');
            clientCodeInput.style.border = '2px solid green';
            clientCodeError.style.display = 'none';
        }
    }

// Закрытие модального окна
    function closeModal() {
        modal.style.display = 'none';
        clientCodeInput.value = '';
        clientCommentInput.value = '';
        clientCompanyInput.value = '';
    }

// Обработчик закрытия модального окна
    closeModalBtn.addEventListener('click', closeModal);
    window.addEventListener('click', function (event) {
        if (event.target === modal) closeModal();
    });

////////////////////////////////////////////////////////////////////
// Открытие модального окна для добавления клиента
    document.getElementById('add-cargo-clients').addEventListener('click', function () {
        openModal();
    });

////////////////////////////////////////////////////////////////////
// Открытие модального окна для редактирования клиента
    document.addEventListener('click', function (event) {
        const button = event.target.closest('.edit-btn');
        if (button) {
            const row = button.closest('tr');
            const clientCode = row.cells[0].innerText;
            const companyName = row.cells[1].innerText;
            const comment = row.cells[2].innerText;
            const clientId = button.getAttribute('data-client-id');
            openModal(clientCode, comment, companyName, clientId);
        }
    });

////////////////////////////////////////////////////////////////////
// Сохранение клиента (универсальная функция для добавления/редактирования)
    saveClientBtn.addEventListener('click', function () {
        const clientCode = clientCodeInput.value.trim();
        const clientComment = clientCommentInput.value.trim();
        const clientCompany = clientCompanyInput.value.trim();
        const originalClientId = modal.getAttribute('data-client-id');

        // Если поля не изменены, просто закрываем модальное окно
        if (!clientCode || clientCodeInput.classList.contains('error')) {
            alert('Введите уникальный код клиента!');
            return;
        }

        // Определяем метод POST для создания или обновления клиента
        const url = originalClientId ? `/cargo/update-client/${originalClientId}/` : '/cargo/add-client/';
        const method = originalClientId ? 'POST' : 'POST';

        fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({
                client_code: clientCode,
                client_comment: clientComment,
                client_company: clientCompany
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (!originalClientId) {
                        // Добавляем нового клиента
                        // Добавляем строку в соответствии с текущей сортировкой
                        const newRow = document.createElement('tr');
                        newRow.classList.add('table-row');

                        // Вставляем содержимое новой строки
                        newRow.innerHTML = `
                        <td>${data.client_code}</td>
                        <td>${data.company_name || 'Нет компании'}</td>
                        <td>${data.comment || ''}</td>
                        <td>
                            <button class="edit-btn" data-client-id="${data.client_id}">
                                <span class="material-icons">edit</span>
                            </button>
                        </td>
                        <td>
                            <button class="delete-btn" data-client-id="${data.client_id}">
                                <span class="material-icons">close</span>
                            </button>
                        </td>
                        `;

// Добавляем строку с учетом сортировки
                        const isAscending = tableHeaders[0].getAttribute('data-sort') === 'asc'; // Проверяем текущее состояние сортировки
                        const rows = Array.from(tableBody.rows);
                        rows.push(newRow); // Добавляем новую строку в конец списка строк

                        rows.sort((rowA, rowB) => {
                            const cellA = rowA.cells[0].innerText.toLowerCase();
                            const cellB = rowB.cells[0].innerText.toLowerCase();
                            if (cellA < cellB) return isAscending ? -1 : 1;
                            if (cellA > cellB) return isAscending ? 1 : -1;
                            return 0;
                        });

// Обновляем таблицу с новой строкой
                        rows.forEach(row => tableBody.appendChild(row));


// Обновляем таблицу с новой строкой
                        rows.forEach(row => tableBody.appendChild(row));

                    } else {
                        // Обновляем существующего клиента
                        const row = document.querySelector(`button[data-client-id='${originalClientId}']`).closest('tr');
                        row.cells[0].innerText = data.client_code;
                        row.cells[1].innerText = data.company_name || 'Нет компании';
                        row.cells[2].innerText = data.comment || '';
                    }
                    closeModal();
                } else {
                    alert('Ошибка при сохранении клиента.');
                }
            })
            .catch(error => {
                console.error('Ошибка при сохранении клиента:', error);
            });
    });

// Обработчик кнопки Удалить
    document.addEventListener('click', function (event) {
        const deleteButton = event.target.closest('.delete-btn');
        if (deleteButton) {
            const row = deleteButton.closest('tr');
            const recordId = deleteButton.getAttribute('data-record-id');  // Универсальный идентификатор записи
            const recordType = deleteButton.getAttribute('data-record-type');  // Тип записи (например, client или product)
            const recordCode = row.cells[0].innerText;  // Код клиента (или другой идентификатор)

            if (!recordId || recordId === 'null') {
                console.error('Ошибка: Невозможно получить ID записи для удаления.');
                return;
            }

            // Открываем модальное окно с подтверждением удаления
            const confirmModal = document.getElementById('deleteConfirmationModal');
            const modalMessage = document.getElementById('modalMessage');
            const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');

            modalMessage.innerText = `Вы действительно хотите удалить ${recordType} с кодом ${recordCode}?`;
            confirmModal.style.display = 'block';

            // Обработка подтверждения удаления
            confirmDeleteBtn.addEventListener('click', function () {
                fetch(`/cargo/delete-${recordType}/${recordId}/`, {  // Динамический URL для удаления
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                    }
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Удаляем строку из таблицы
                            row.remove();
                            confirmModal.style.display = 'none';
                        } else if (data.dependencies) {
                            alert(`Невозможно удалить, так как запись используется в: ${data.dependencies.join(', ')}`);
                        } else {
                            alert('Ошибка при удалении записи.');
                        }
                    })
                    .catch(error => {
                        console.error('Ошибка при удалении записи:', error);
                        alert('Произошла ошибка при удалении.');
                    });
            }, {once: true});
        }
    });

// Проверка уникальности кода клиента при каждом вводе символа
    clientCodeInput.addEventListener('input', function () {
        const clientCode = clientCodeInput.value.trim();
        const clientId = modal.getAttribute('data-client-id');

        const excludeParam = clientId && clientId !== 'null' ? `&exclude_id=${clientId}` : '';

        fetch(`/cargo/check-client-code/?code=${encodeURIComponent(clientCode)}${excludeParam}`)
            .then(response => response.json())
            .then(data => {
                if (!data.is_unique) {
                    clientCodeInput.classList.add('error');
                    clientCodeInput.style.border = '2px solid red';
                    clientCodeError.textContent = 'Код клиента уже используется';
                    clientCodeError.style.display = 'block';
                } else {
                    clientCodeInput.classList.remove('error');
                    clientCodeInput.style.border = '2px solid green';
                    clientCodeError.style.display = 'none';
                }
            })
            .catch(error => {
                console.error('Ошибка при проверке уникальности кода клиента:', error);
            });
    });

// Открытие списка компаний при фокусе на поле Компания
    clientCompanyInput.setAttribute('autocomplete', 'off');

    clientCompanyInput.addEventListener('focus', function () {
        fetch('/cargo/get-companies/')
            .then(response => response.json())
            .then(data => {
                const companyList = document.getElementById('company-list');
                companyList.innerHTML = '';  // Очищаем старые опции

                data.companies.forEach(company => {
                    const option = document.createElement('option');
                    option.value = company.company_name;
                    companyList.appendChild(option);
                });
            })
            .catch(error => {
                console.error('Ошибка при загрузке списка компаний:', error);
            });
    });

////////////////////////////////////////////////////////////////////
// Функция для получения CSRF-токена
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const addProductBtn = document.getElementById('add-cargo-products');
    const productModal = document.getElementById('productsModal');
    const closeProductModalBtn = document.getElementById('closeProductModal');
    const saveProductBtn = document.getElementById('save-product-btn');
    const productCodeInput = document.getElementById('productCode');
    const productCodeError = document.getElementById('productCodeError');
    const productClientInput = document.getElementById('productClient');
    const productCategoryInput = document.getElementById('productCategory');
    const clientList = document.getElementById('client-list');
    const categoryList = document.getElementById('category-list');
   const addProductBtn = document.getElementById('add-cargo-products');
    const productModal = document.getElementById('productsModal');

    // Проверка на наличие элемента перед добавлением обработчика
    if (addProductBtn && productModal) {
        addProductBtn.addEventListener('click', function () {
            productModal.style.display = 'block';

            // Очистка полей в модальном окне
            document.getElementById('productCode').value = '';
            document.getElementById('productName').value = '';
            document.getElementById('productPrice').value = '';
            document.getElementById('productCategory').value = '';
            document.getElementById('productClient').value = '';

            // Сброс возможных сообщений об ошибках
            const productCodeError = document.getElementById('productCodeError');
            if (productCodeError) {
                productCodeError.style.display = 'none';
            }
        });
    } else {
        console.error('Элемент с ID "add-cargo-products" или "productsModal" не найден.');
    }
    // Открыть модальное окно при нажатии кнопки "Добавить"
    addProductBtn.addEventListener('click', function () {
        productModal.style.display = 'block';

        // Загрузка клиентов в список для выбора
        fetch('/api/clients/')
            .then(response => response.json())
            .then(data => {
                clientList.innerHTML = '';
                data.forEach(client => {
                    const option = document.createElement('option');
                    option.value = client.name;
                    clientList.appendChild(option);
                });
            });

        // Загрузка категорий в список для выбора
        fetch('/api/categories/')
            .then(response => response.json())
            .then(data => {
                categoryList.innerHTML = '';
                data.forEach(category => {
                    const option = document.createElement('option');
                    option.value = category.name;
                    categoryList.appendChild(option);
                });
            });
    });

     Закрытие модального окна "Товары"
    const closeProductModalBtn = document.getElementById('closeProductModal');
    if (closeProductModalBtn && productModal) {
        closeProductModalBtn.addEventListener('click', function () {
            productModal.style.display = 'none';
        });
    } else {
        console.error('Элемент с ID "closeProductModal" не найден.');
    }

    // Контроль уникальности для поля "Код Товара"
    productCodeInput.addEventListener('blur', function () {
        const productCode = productCodeInput.value;
        if (productCode) {
            fetch(`/api/check-product-code/?code=${productCode}`)
                .then(response => response.json())
                .then(data => {
                    if (data.exists) {
                        productCodeError.style.display = 'inline';
                    } else {
                        productCodeError.style.display = 'none';
                    }
                });
        }
    });

    // Сохранение нового товара
    saveProductBtn.addEventListener('click', function () {
        const productCode = productCodeInput.value;
        const productName = document.getElementById('productName').value;
        const productPrice = document.getElementById('productPrice').value;
        const productCategory = productCategoryInput.value;
        const productClient = productClientInput.value;

        if (!productCode || !productName || !productPrice || !productCategory || !productClient) {
            alert('Пожалуйста, заполните все поля.');
            return;
        }

        // Отправляем данные на сервер для сохранения
        fetch('/api/products/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                code: productCode,
                name: productName,
                price: productPrice,
                category: productCategory,
                client: productClient
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Товар успешно добавлен');
                    productModal.style.display = 'none';
                    // Очистить форму
                    productCodeInput.value = '';
                    document.getElementById('productName').value = '';
                    document.getElementById('productPrice').value = '';
                    productCategoryInput.value = '';
                    productClientInput.value = '';
                } else {
                    alert('Ошибка при добавлении товара');
                }
            });
    });
});

// Открытие модального окна для добавления товара
document.getElementById('add-cargo-products').addEventListener('click', function () {
    const productModal = document.getElementById('productsModal');
    productModal.style.display = 'block';

    // Установка начальных значений полей
    document.getElementById('productCode').value = '';
    document.getElementById('productName').value = '';
    document.getElementById('productPrice').value = '';
    document.getElementById('productCategory').value = '';
    document.getElementById('productClient').value = '';

    // Обнуляем возможные сообщения об ошибках
    const productCodeError = document.getElementById('productCodeError');
    productCodeError.style.display = 'none';
});

// Сохранение товара
const saveProductBtn = document.getElementById('save-product-btn');
saveProductBtn.addEventListener('click', function () {
    const productCode = document.getElementById('productCode').value.trim();
    const productName = document.getElementById('productName').value.trim();
    const productPrice = document.getElementById('productPrice').value.trim();
    const productCategory = document.getElementById('productCategory').value.trim();
    const productClient = document.getElementById('productClient').value.trim();

    // Проверяем, что все поля заполнены
    if (!productCode || !productName || !productPrice || !productCategory || !productClient || productCodeInput.classList.contains('error')) {
        alert('Пожалуйста, заполните все поля корректно!');
        return;
    }

    fetch('/cargo/add-product/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({
            product_code: productCode,
            product_name: productName,
            product_price: productPrice,
            product_category: productCategory,
            product_client: productClient
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Товар успешно добавлен');
                const productModal = document.getElementById('productsModal');
                productModal.style.display = 'none';
                // Очистка формы
                productCodeInput.value = '';
                document.getElementById('productName').value = '';
                document.getElementById('productPrice').value = '';
                document.getElementById('productCategory').value = '';
                document.getElementById('productClient').value = '';
            } else {
                alert('Ошибка при добавлении товара');
            }
        })
        .catch(error => {
            console.error('Ошибка при добавлении товара:', error);
        });
});


// Закрытие модального окна
document.getElementById('closeProductModal').addEventListener('click', function () {
    const productModal = document.getElementById('productsModal');
    productModal.style.display = 'none';
});
