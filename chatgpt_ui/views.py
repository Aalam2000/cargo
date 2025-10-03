import json
import os
import re
import uuid

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
from openai import OpenAI

# Загрузка ключа OpenAI
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OpenAI API ключ не найден. Проверьте файл .env.")

client = OpenAI(api_key=api_key)

# История диалога
conversation = []


# def dialog_view(request):
#     return render(request, 'chatgpt_ui/dialog.html')


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
                model="gpt-4o",
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
