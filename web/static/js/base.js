// ========= Общие функции для сайта =========

// Отправка формы выхода
function logoutUser() {
    const form = document.getElementById('logout-form');
    if (form) form.submit();
}

// Подсветка активного пункта меню
function highlightActiveLink() {
    const links = document.querySelectorAll('.menu-item');
    const current = window.location.pathname;
    links.forEach(link => {
        if (link.getAttribute('href') === current) {
            link.classList.add('active');
        }
    });
}

// Показ уведомлений (всплывающие подсказки)
function showMessage(type, text) {
    const box = document.createElement('div');
    box.className = `message ${type}`;
    box.textContent = text;
    document.body.appendChild(box);
    setTimeout(() => box.classList.add('show'), 100);
    setTimeout(() => box.classList.remove('show'), 3000);
    setTimeout(() => box.remove(), 3500);
}

// ======= Управление боковой панелью =======
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;

    // мобильная ширина ≤ 900px — работает как выезжающая панель
    if (window.innerWidth <= 900) {
        sidebar.classList.toggle('open');
    }
    // десктоп — просто сворачивание панели
    else {
        sidebar.classList.toggle('collapsed');
    }
}


// ======= Автоматическое скрытие панели =======
document.addEventListener('click', (e) => {
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar || !sidebar.classList.contains('open')) return;

    const clickedInside = e.target.closest('.sidebar') || e.target.closest('#burger');
    if (!clickedInside) {
        sidebar.classList.remove('open'); // клик вне панели — закрыть
    }

    // при клике на пункт меню, кнопку логина или универсальную кнопку
    if (e.target.closest('.menu-item, .login-form button, .btn')) {
        sidebar.classList.remove('open');
    }
});

// ======= Аккордеон для разделов =======
function toggleAccordion(header) {
    const accordion = header.parentElement;
    accordion.classList.toggle('open');
}

// ======= Инициализация =======
document.addEventListener('DOMContentLoaded', () => {
    highlightActiveLink();
});
