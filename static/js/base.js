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

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
  highlightActiveLink();
});
