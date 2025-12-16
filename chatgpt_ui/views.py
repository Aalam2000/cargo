# chatgpt_ui/views.py

import json
import os
import re
import uuid
from typing import List, cast

import requests
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from accounts.services.client_actions import safe_parse_ai_json, create_client_with_user
from .models import ChatSession

# Загрузка ключа OpenAI
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OpenAI API ключ не найден. Проверьте файл .env.secrets")

client = OpenAI(api_key=api_key)

# История диалога
conversation = []


def get_mac_address(request):
    try:
        # Получение MAC-адреса сервера для тестирования
        mac = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
        return JsonResponse({'mac': mac})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    # todo: Не тот мак адрес берется. Надо убрать.


def load_history():
    """Загружает историю диалога из файла."""
    global conversation
    try:
        with open("conversation_history.json", "r", encoding="utf-8") as file:
            conversation = json.load(file)
    except FileNotFoundError:
        conversation = [{"role": "system", "content": "Ты помощник разработчика."}]


def save_history():
    """Сохраняет историю диалога в файл."""
    with open("conversation_history.json", "w", encoding="utf-8") as file:
        json.dump(conversation, file, ensure_ascii=False, indent=4)


def load_manuals():
    """Загружает индекс мануалов."""
    manuals_index_path = os.path.join(settings.BASE_DIR, "manuals", "index.json")
    try:
        with open(manuals_index_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        print("Индекс мануалов не найден. Создайте его с помощью index_builder.py.")
        return {}


def load_project_index():
    """Загружает индекс проекта."""
    project_index_path = os.path.join(settings.BASE_DIR, "project_index.json")
    try:
        with open(project_index_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        print("Индекс проекта не найден. Создайте его с помощью index_builder.py.")
        return {}


def search_in_index(query, index):
    """Интеллектуальный поиск в проекте."""
    results = []
    query_lower = query.lower()

    # Проверяем, есть ли запрос, связанный с таблицей
    if "таблица" in query_lower or "table" in query_lower:
        # Поиск таблицы в HTML-файлах
        for file_path, details in index["details"].items():
            if file_path.endswith(".html") and "product-table" in details["excerpt"]:
                results.append(f"Таблица найдена в HTML-файле: {file_path}")

                # Анализ подключенных JS-файлов
                connected_js = find_connected_js(file_path, details["excerpt"])
                for js_file in connected_js:
                    js_functions = find_table_functions(js_file, "product-table")
                    if js_functions:
                        results.extend(js_functions)

    return results


def find_file_in_project(file_name, base_dir, excluded_dirs=None):
    """
    Ищет файл с указанным именем во всех папках проекта.
    :param file_name: Имя файла для поиска.
    :param base_dir: Базовая директория проекта.
    :param excluded_dirs: Список директорий, которые нужно игнорировать.
    :return: Путь к найденному файлу или None.
    """
    if excluded_dirs is None:
        excluded_dirs = ["venv", "__pycache__", "staticfiles", ".git"]

    for root, dirs, files in os.walk(base_dir):
        # Исключаем нежелательные директории
        dirs[:] = [d for d in dirs if d not in excluded_dirs]

        if file_name in files:
            return os.path.join(root, file_name)

    return None


def analyze_specific_file(file_path, keyword=None):
    """Читает указанный файл и ищет ключевые слова, если они заданы."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        if keyword:
            # Ищем все упоминания ключевого слова
            matches = re.findall(rf"{re.escape(keyword)}", content)
            if matches:
                return f"Ключевое слово '{keyword}' найдено в файле {file_path}.\nСодержимое: \n{content}"
            else:
                return f"Ключевое слово '{keyword}' не найдено в файле {file_path}."
        else:
            return f"Содержимое файла {file_path}: \n{content}"

    except FileNotFoundError:
        return f"Файл {file_path} не найден."
    except Exception as e:
        return f"Ошибка при анализе файла {file_path}: {str(e)}"


def analyze_file_content(file_path, keyword=None):
    """
    Читает содержимое найденного файла и ищет ключевое слово, если оно задано.
    :param file_path: Путь к файлу.
    :param keyword: Ключевое слово для поиска.
    :return: Результат анализа файла.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        if keyword:
            matches = re.findall(rf"{re.escape(keyword)}", content, re.IGNORECASE)
            if matches:
                return f"Ключевое слово '{keyword}' найдено в файле {file_path}.\nСодержимое: \n{content}"
            else:
                return f"Ключевое слово '{keyword}' не найдено в файле {file_path}."
        else:
            return f"Содержимое файла {file_path} : \n{content}"

    except Exception as e:
        return f"Ошибка при анализе файла {file_path}: {str(e)}"


def find_connected_js(html_path, html_content):
    """Ищет подключенные JS-файлы в HTML."""
    connected_js = []
    script_pattern = r'<script src="{% static \'(.+\.js)\' %}">'
    matches = re.findall(script_pattern, html_content)

    for match in matches:
        js_file = os.path.join(settings.BASE_DIR, "static", match)
        connected_js.append(js_file)

    return connected_js


def find_table_functions(js_path, table_id):
    """Ищет функции, связанные с таблицей, в JS-файле."""
    functions = []
    try:
        with open(js_path, "r", encoding="utf-8") as js_file:
            content = js_file.read()

        # Ищем функции, работающие с таблицей
        if table_id in content:
            function_pattern = r'function\s+(\w+)\s*\(.*?\)\s*{'
            matches = re.findall(function_pattern, content)

            for match in matches:
                functions.append(f"Функция '{match}' найдена в {js_path}")

    except FileNotFoundError:
        print(f"Файл {js_path} не найден.")

    return functions


def add_message(role, content):
    """Добавляет сообщение в историю беседы."""
    conversation.append({"role": role, "content": content})


# Загрузка истории при запуске сервера
load_history()


def build_client_parser_prompt() -> str:
    return """
Вы — парсер команд CargoAdmin.

Вам приходит ТЕКСТ пользователя на ЛЮБОМ языке (любой формат).
Нужно определить, просит ли пользователь СОЗДАТЬ/ПРИГЛАСИТЬ КЛИЕНТА по e-mail.

ДОСТУПНЫЕ ДЕЙСТВИЯ:
- "create_client" — пользователь явно хочет создать/пригласить клиента
  (сообщение про клиента и в нём есть e-mail: слова типа
   "клиент", "client", "customer", "müşteri" и т.п., либо по смыслу
   понятно, что это новый клиент платформы).
- "unknown" — все остальные случаи.

ОТВЕЧАЙТЕ ТОЛЬКО JSON, БЕЗ ТЕКСТА ВНЕ JSON:

{
  "action": "...",
  "email": "...",
  "name": "..."
}

ПРАВИЛА ФОРМИРОВАНИЯ:
- email — первый найденный корректный e-mail или пустая строка.
- name — имя/название клиента, если явно указано в тексте, иначе пустая строка.
- Если НЕТ валидного e-mail ИЛИ не видно запроса на создание/приглашение клиента —
  верните:

{
  "action": "unknown",
  "email": "",
  "name": ""
}

ПРИМЕРЫ:

INPUT: "клиент motopara@gmail.com"
OUTPUT:
{
  "action": "create_client",
  "email": "motopara@gmail.com",
  "name": ""
}

INPUT: "создай нового клиента Иван Иванов, почта ivan@example.com"
OUTPUT:
{
  "action": "create_client",
  "email": "ivan@example.com",
  "name": "Иван Иванов"
}

INPUT: "привет, какая сегодня погода?"
OUTPUT:
{
  "action": "unknown",
  "email": "",
  "name": ""
}
"""


def call_openai_with_prompt(system_prompt: str, user_text: str) -> str:
    messages = cast(
        List[ChatCompletionMessageParam],
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
    )
    content = response.choices[0].message.content
    return content or ""


@csrf_exempt
def dialog_view(request):
    if request.method == 'POST':
        user_message = request.POST.get('message', '').strip()
        if not user_message:
            return JsonResponse({"error": "Сообщение не может быть пустым."}, status=400)

        add_message("user", user_message)

        try:
            # Проверяем, указан ли файл в запросе
            if "в файле" in user_message.lower():
                file_match = re.search(r"в файле ([\w/.\-]+)", user_message.lower())
                keyword_match = re.search(r"используют ([\w_]+)", user_message.lower())

                if file_match:
                    file_name = file_match.group(1).strip()
                    keyword = keyword_match.group(1).strip() if keyword_match else None

                    # Ищем файл во всем проекте
                    base_dir = settings.BASE_DIR
                    file_path = find_file_in_project(file_name, base_dir)

                    if file_path:
                        # Анализируем содержимое найденного файла
                        analysis_result = analyze_file_content(file_path, keyword)
                        return JsonResponse({"message": analysis_result})
                    else:
                        return JsonResponse({"message": f"Файл {file_name} не найден в проекте."})

            # Стандартный процесс обработки запросов
            response = client.chat.completions.create(
                model="gpt-5.1",
                messages=conversation
            )

            assistant_message = response.choices[0].message.content
            add_message("assistant", assistant_message)
            save_history()

            return JsonResponse({"message": assistant_message})

        except Exception as e:
            print(f"Ошибка OpenAI: {str(e)}")
            return JsonResponse({"error": f"Ошибка OpenAI: {str(e)}"}, status=500)

    return render(request, 'chatgpt_ui/dialog.html')


@csrf_exempt
def tg_webhook(request):
    if request.method != "POST":
        return JsonResponse({"status": "ok"})

    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"status": "invalid_json"})

    message = data.get("message", {})
    text = (message.get("text") or "").strip()
    chat = message.get("chat", {})

    telegram_id = str(chat.get("id")) if chat else None
    username = chat.get("username")
    first_name = chat.get("first_name")
    last_name = chat.get("last_name")

    if not telegram_id or not text:
        return JsonResponse({"status": "ignored"})

    # --- Сессия Telegram ---
    session, _ = ChatSession.objects.get_or_create(telegram_id=telegram_id)

    # --- Определение пользователя по accounts_customuser.telegram ---
    from accounts.models import CustomUser

    matched_user = None
    incoming = set()
    if username:
        incoming.add(username.lower())
    if telegram_id:
        incoming.add(telegram_id.lower())

    for u in CustomUser.objects.all():
        if not u.telegram:
            continue
        val = u.telegram.strip().lower().replace("@", "")
        if val in incoming:
            matched_user = u
            break

    if matched_user and not session.user:
        session.user = matched_user
        session.save()

    # --- Пользователь не опознан ---
    if not session.user:
        show_username = f"@{username}" if username else "нет"
        details = (
            "Добро пожаловать в CargoAdmin Bot!\n\n"
            "Ваш Telegram ещё не привязан к системе.\n"
            "Откройте CargoAdmin и заполните поле «Telegram» в карточке пользователя.\n\n"
            "Укажите одно из значений:\n"
            f"• {show_username}\n"
            f"• {telegram_id}\n\n"
            "Ссылка на платформу:\nhttps://bonablog.ru\n\n"
            "Ваши данные:\n"
            f"ID: {telegram_id}\n"
            f"Username: {show_username}\n"
            f"Имя: {first_name or 'нет'}\n"
            f"Фамилия: {last_name or 'нет'}"
        )
        return send_tg_reply(telegram_id, details)

    # --- Права ---
    if session.user.role not in ("Admin", "Operator"):
        return send_tg_reply(
            telegram_id,
            "У вас нет прав для создания или приглашения клиентов."
        )

    # --- Парсинг сообщения через OpenAI (ВСЕГДА) ---
    parser_prompt = build_client_parser_prompt()
    try:
        ai_answer = call_openai_with_prompt(parser_prompt, text)
    except Exception:
        ai_answer = '{"action":"unknown","email":"","name":""}'

    data = safe_parse_ai_json(ai_answer)

    # --- Реакция только на create_client ---
    if (data.get("action") or "").strip() == "create_client" and (data.get("email") or "").strip():
        # Пока используем существующий preview (по текущему проекту)
        result_text = create_client_with_user(
            email=data["email"],
            name=data.get("name", ""),
            operator_user=session.user,
        )
        return send_tg_reply(telegram_id, result_text)

    # --- Иначе — нейтральный ответ ---
    if first_name or last_name:
        name_block = f"{first_name or ''} {last_name or ''}".strip()
    elif username:
        name_block = f"@{username}"
    else:
        name_block = f"ID {telegram_id}"

    return send_tg_reply(
        telegram_id,
        f"Принял, {name_block}. Если нужно создать клиента — напишите сообщение с e-mail клиента."
    )



# --- Функция отправки сообщений в Telegram ---
def send_tg_reply(chat_id, text):
    token = os.getenv("ADMIN_BOT_TG")
    if not token:
        print("ERROR: ADMIN_BOT_TG env variable is missing!")
        return JsonResponse({"status": "no_token"})

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text
    }

    try:
        r = requests.post(url, json=payload, timeout=5)
        print("TG SEND RESPONSE:", r.status_code, r.text)
    except Exception as e:
        print("TG SEND ERROR:", e)
        return JsonResponse({"status": "error", "detail": str(e)})

    return JsonResponse({"status": "sent"})
