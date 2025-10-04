import os
import sys
import json
import getpass
import platform
import socket
import psycopg2
from datetime import datetime, UTC
from pathlib import Path
from dotenv import load_dotenv

# === 1. Загрузка переменных окружения ===
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)

# === 2. Основные переменные ===
SERVER_DB = {
    "host": os.getenv("IP_POSTGRES"),
    "port": os.getenv("DB_PORT", "5432"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "dbname": os.getenv("DB_NAME"),
}

LOCAL_DB = {
    "host": "localhost",
    "port": "5432",
    "user": "dev_user",
    "password": "dev_pass",
    "dbname": "cargo_dev",
}

# === 3. Функция проверки соединения ===
def test_connection(cfg: dict):
    result = {
        "host": cfg["host"],
        "port": cfg["port"],
        "dbname": cfg["dbname"],
        "user": cfg["user"],
        "status": "unknown",
        "error": None,
    }
    try:
        conn = psycopg2.connect(
            host=cfg["host"],
            port=cfg["port"],
            user=cfg["user"],
            password=cfg["password"],
            dbname=cfg["dbname"],
            connect_timeout=3
        )
        conn.close()
        result["status"] = "ok"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    return result

# === 4. Проверки ===
server_check = test_connection(SERVER_DB)
local_check = test_connection(LOCAL_DB)

# === 5. Общая информация ===
info = {
    "timestamp": datetime.now(UTC).isoformat(),
    "project_root": str(Path(__file__).resolve().parents[1]),
    "env_file": str(env_path),
    "system_user": getpass.getuser(),
    "python_version": sys.version,
    "os": platform.platform(),
    "hostname": socket.gethostname(),
    "ip_local": socket.gethostbyname(socket.gethostname()),
    "checks": {
        "local_docker_db": local_check,
        "server_prod_db": server_check
    },
    "instructions": """
Этот файл создан для анализа конфигурации перед переходом на Docker.

1️⃣ Сейчас проект работает напрямую с Postgres на сервере (server_prod_db).
   После перехода Docker должен использовать ЛОКАЛЬНЫЙ контейнер Postgres для разработки.

2️⃣ Как переходить:
   - Создать docker-compose.dev.yml:
       services:
         app:
           build: .
           env_file: .env
           ports:
             - "8000:8000"
           depends_on:
             - db
         db:
           image: postgres:15
           environment:
             POSTGRES_USER: dev_user
             POSTGRES_PASSWORD: dev_pass
             POSTGRES_DB: cargo_dev
           ports:
             - "5432:5432"
           volumes:
             - pgdata:/var/lib/postgresql/data
       volumes:
         pgdata:

   - На сервере останется системный Postgres, подключаемый через docker-compose.prod.yml (без контейнера db).
   - Переменные в .env определяют, к какой БД идёт подключение.
   - Для dev-окружения база в контейнере (localhost), для prod — внешняя (185.169.54.164).

3️⃣ После создания docker-compose.dev.yml запусти:
   docker compose -f docker-compose.dev.yml up --build
   И проверь этим же скриптом, что соединение прошло к localhost.
"""
}

# === 6. Сохранение ===
out_file = Path(__file__).with_name("analyze_result.json")
with out_file.open("w", encoding="utf-8") as f:
    json.dump(info, f, indent=2, ensure_ascii=False)

print(f"[INFO] Отчёт сохранён в {out_file}")
