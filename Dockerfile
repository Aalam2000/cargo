FROM python:3.12-slim

# system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 libcairo2-dev \
    libpango-1.0-0 libpangocairo-1.0-0 libpangoft2-1.0-0 \
    libgdk-pixbuf-2.0-0 gdk-pixbuf2.0-bin gdk-pixbuf2.0-common \
    libjpeg-dev libpng-dev libffi-dev shared-mime-info fonts-dejavu-core \
    gcc libpq-dev postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ✅ КОД ДОЛЖЕН БЫТЬ В IMAGE
COPY . .

ENV DJANGO_SETTINGS_MODULE=cargodb.settings

# collectstatic — ТОЛЬКО прод
ARG ENVIRONMENT=dev
ENV ENVIRONMENT=${ENVIRONMENT}

RUN if [ "$ENVIRONMENT" = "production" ]; then \
        python manage.py collectstatic --noinput ; \
    else \
        echo "Dev mode — collectstatic skipped" ; \
    fi

CMD ["gunicorn", "cargodb.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "60"]
