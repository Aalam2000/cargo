// Функции для работы с модальными окнами

// Открытие модального окна
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
    } else {
        console.error(`Модальное окно с ID ${modalId} не найдено.`);
    }
}

// Закрытие модального окна
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    } else {
        console.error(`Модальное окно с ID ${modalId} не найдено.`);
    }
}

// Очистка полей в модальном окне
function resetModalFields(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        const inputs = modal.querySelectorAll('input');
        inputs.forEach(input => {
            input.value = '';
        });

        const errorMessages = modal.querySelectorAll('.error-message');
        errorMessages.forEach(error => {
            error.style.display = 'none';
        });
    }
}

// Отправка данных формы модального окна
function submitModalForm(modalId, formData) {
    // Здесь можно добавить код для отправки данных формы на сервер
    console.log(`Отправка данных формы из модального окна ${modalId}:`, formData);
}

// Пример кода для открытия модального окна "Добавить товар"
document.addEventListener('DOMContentLoaded', function () {
    const addProductBtn = document.getElementById('add-cargo-products');
    if (addProductBtn) {
        addProductBtn.addEventListener('click', function () {
            openModal('productsModal');
            resetModalFields('productsModal');
        });
    }

    // Закрытие модального окна
    const closeProductModalBtn = document.getElementById('closeProductModal');
    if (closeProductModalBtn) {
        closeProductModalBtn.addEventListener('click', function () {
            closeModal('productsModal');
        });
    }

    // Пример сохранения данных из формы модального окна "Товары"
    const saveProductBtn = document.getElementById('save-product-btn');
    if (saveProductBtn) {
        saveProductBtn.addEventListener('click', function () {
            const productCode = document.getElementById('productCode').value.trim();
            const productName = document.getElementById('productName').value.trim();
            const productPrice = document.getElementById('productPrice').value.trim();
            const productCategory = document.getElementById('productCategory').value.trim();
            const productClient = document.getElementById('productClient').value.trim();

            if (!productCode || !productName || !productPrice || !productCategory || !productClient) {
                alert('Пожалуйста, заполните все поля.');
                return;
            }

            const formData = {
                productCode,
                productName,
                productPrice,
                productCategory,
                productClient
            };

            // Здесь вызывается функция для отправки данных
            submitModalForm('productsModal', formData);
        });
    }
});
