let currentPage = 1;
const pageSize = 15;
let loading = false;

async function loadTable() {
    try {
        const response = await fetch(`/cargo_acc/client_table/data/`);
        if (!response.ok) throw new Error(`Ошибка: ${response.status}`);

        const {results} = await response.json();
        const tableBody = document.querySelector('#client-table tbody');
        const fragment = document.createDocumentFragment();

        results.forEach(item => {
            const row = document.createElement('tr');
            row.classList.add('table-row');
            row.setAttribute('data-model', item.model); // Устанавливаем модель для строки

            row.innerHTML = `
                <td>${item.client_code}</td>
                <td>${item.company}</td>
                <td>${item.description}</td>
                <td class="delete-cell">
                    <i class="fa fa-trash"></i> <!-- Кнопка удаления -->
                </td>
           `;

            // Привязываем универсальную функцию удаления
            row.querySelector('.fa-trash').onclick = () => deleteRow('Client', row);

            fragment.appendChild(row);
        });


        tableBody.appendChild(fragment);

    } catch (error) {
        console.error('Ошибка загрузки таблицы:', error);
    }
}

// Универсальная функция для настройки кнопок "Отмена"
function setupCancelButtons() {
    const cancelButtons = document.querySelectorAll('.btn-cancel');
    cancelButtons.forEach(button => {
        button.onclick = () => {
            const modal = button.closest('.modal'); // Находим родительское модальное окно

            // Перемещаем фокус на безопасный элемент перед скрытием модального окна
            const focusTarget = document.body; // Переводим фокус на body или другой доступный элемент
            focusTarget.focus(); // Гарантируем смену фокуса

            // Используем requestAnimationFrame для плавного закрытия
            requestAnimationFrame(() => {
                modal.style.display = 'none'; // Закрываем модальное окно
                modal.setAttribute('aria-hidden', 'true'); // Скрываем его от вспомогательных технологий
            });
        };
    });
}

document.addEventListener('DOMContentLoaded', () => {
    loadTable();  // Загрузка всей таблицы при открытии страницы

    const filterInput = document.getElementById('client-filter');
    filterInput.addEventListener('input', () => {
        filterTable('client-table', filterInput.value);
    });

    document.querySelector('#client-table').addEventListener('click', event => {
        if (event.target.classList.contains('fa-trash')) {
            const row = event.target.closest('tr');
            const clientName = row.cells[1].textContent; // Получаем название компании
            openDeleteModal(clientName, row);
        }
    });
    setupCancelButtons();  // Настраиваем кнопки "Отмена"
});

function openDeleteModal(clientName, row) {
    const modal = document.getElementById('deleteModal');
    const modalMessage = modal.querySelector('.modal-message');
    modalMessage.textContent = `Вы действительно хотите удалить клиента "${clientName}"?`;

    const confirmButton = modal.querySelector('#confirmDeleteButton');
    confirmButton.onclick = () => {
        const modelName = row.getAttribute('data-model'); // Получаем имя модели из строки
        deleteRow(modelName, row); // Удаляем строку с учётом модели
        modal.style.display = 'none'; // Закрываем модальное окно после удаления
    };

    const closeButton = modal.querySelector('.close');
    closeButton.onclick = () => {
        modal.style.display = 'none'; // Закрываем модальное окно при нажатии на "Закрыть"
    };

    modal.style.display = 'block'; // Открываем модальное окно
}


async function deleteRow(modelName, row) {
    const rowId = row.getAttribute('data-id'); // Предполагаем, что ID хранится в атрибуте data-id

    try {
        const response = await fetch(`/api/delete/${modelName}/${rowId}/`, {
            method: 'DELETE',
            headers: {'Content-Type': 'application/json'},
        });

        if (!response.ok) {
            throw new Error(`Ошибка удаления: ${response.statusText}`);
        }
        row.remove(); // Удаляем строку из таблицы при успешном удалении
    } catch (error) {
        console.error('Ошибка при удалении строки:', error);
    }
}


function filterTable(tableId, query) {
    const table = document.getElementById(tableId);
    const rows = table.querySelectorAll('tbody tr');
    query = query.toLowerCase();

    rows.forEach(row => {
        const clientCode = row.querySelector('td').textContent.toLowerCase();
        row.style.display = clientCode.includes(query) ? '' : 'none';
    });
}