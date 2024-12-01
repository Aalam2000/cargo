document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('chat-form');
    const output = document.getElementById('chat-output');
    const loadingIndicator = document.getElementById('loading-indicator');
    const submitButton = document.getElementById('submit-btn');

    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        const formData = new FormData(form);
        const userMessage = formData.get('message');

        // Добавляем пользовательское сообщение в интерфейс
        const userDiv = document.createElement('div');
        userDiv.className = 'user-message';
        userDiv.textContent = `Вы: ${userMessage}`;
        output.appendChild(userDiv);

        // Показываем индикатор загрузки и блокируем кнопку
        loadingIndicator.style.display = 'block';
        submitButton.disabled = true;

        try {
            const response = await fetch('', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            });

            if (!response.ok) {
                throw new Error(`Ошибка HTTP: ${response.status}`);
            }

            const data = await response.json();

            if (data.message) {
                const botDiv = document.createElement('div');
                botDiv.className = 'bot-message';
                botDiv.textContent = `Bot: ${data.message}`;
                output.appendChild(botDiv);
            } else if (data.error) {
                alert(`Ошибка: ${data.error}`);
            }
        } catch (error) {
            console.error('Ошибка:', error);
        } finally {
            // Скрываем индикатор загрузки и разблокируем кнопку
            loadingIndicator.style.display = 'none';
            submitButton.disabled = false;
        }

        form.reset();
    });
});
