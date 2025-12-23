#Dockerfile
FROM python:3.12-slim

# =====================================================================
# 1) ОБЯЗАТЕЛЬНЫЕ СИСТЕМНЫЕ БИБЛИОТЕКИ ДЛЯ WEASYPRINT
# =====================================================================
# Cairo + Pango + Pixbuf + PNG/JPEG loaders
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libcairo2-dev \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    gdk-pixbuf2.0-bin \
    gdk-pixbuf2.0-common \
    libjpeg-dev \
    libpng-dev \
    libffi-dev \
    shared-mime-info \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# =====================================================================
# 2) БИБЛИОТЕКИ ДЛЯ psycopg2
# =====================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# =====================================================================
# 3) Установка Python-зависимостей
# =====================================================================
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# =====================================================================
# 4) Копирование проекта
# =====================================================================
COPY . .

ENV DJANGO_SETTINGS_MODULE=cargodb.settings

# =====================================================================
# 5) Collectstatic — только на продакшене
# =====================================================================
ARG ENVIRONMENT=dev
ENV ENVIRONMENT=${ENVIRONMENT}

RUN if [ "$ENVIRONMENT" = "production" ] ; then \
        python manage.py collectstatic --noinput ; \
    else \
        echo "Dev mode — collectstatic пропущен"; \
    fi

# =====================================================================
# 6) Команда запуска
# =====================================================================
CMD ["gunicorn", "cargodb.wsgi:application", "--bind", "0.0.0.0:8000"]
