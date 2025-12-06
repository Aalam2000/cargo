# Dockerfile
FROM python:3.12-slim
# === WeasyPrint system deps ===
RUN apt-get update && apt-get install -y \
    libcairo2 \
    libcairo2-dev \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Системные зависимости для psycopg2
RUN apt-get update && apt-get install -y gcc libpq-dev postgresql-client && rm -rf /var/lib/apt/lists/*

# Устанавливаем зависимости Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Указываем переменные среды для Django
ENV DJANGO_SETTINGS_MODULE=cargodb.settings

# Собираем статику (теперь корректно, т.к. проект уже скопирован)
RUN python manage.py collectstatic --noinput || true

# Запуск gunicorn
CMD ["gunicorn", "cargodb.wsgi:application", "--bind", "0.0.0.0:8000"]
