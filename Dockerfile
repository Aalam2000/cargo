FROM python:3.12-slim

WORKDIR /app

# Устанавливаем системные зависимости (для psycopg2)
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Собираем статику
RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "cargodb.wsgi:application", "--bind", "0.0.0.0:8000"]
