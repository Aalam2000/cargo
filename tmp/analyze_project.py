import fnmatch
import json
import os
import platform
import subprocess

# Укажите корневую директорию проекта
PROJECT_ROOT = "C:/Users/Papa/PycharmProjects/cargodb"
OUTPUT_FILE = "project_structure.json"

# Список директорий для исключения (без содержимого)
EXCLUDED_DIRS = [
    # "accounts",
    "management",
    "migrations",
    # "cargo_acc",
    # "cargodb",
    "chatgpt_ui",
    "home",
    "img",
    "manuals",
    "media",
    # "static",
    "staticfiles",
    # "templates",
    "test",
    "venv",
    ".git",
    ".idea",
    "__pycache__"
]

# Список файлов для включения с содержимым (относительные пути от PROJECT_ROOT)
INCLUDE_CONTENT = [
    # "manage.py",
    # "cargodb/settings.py",
    # "cargodb/urls.py",
    # "cargodb/views.py",
    # "cargo_acc/urls.py",
    # "cargo_acc/models.py",
    # "cargo_acc/views.py",
    # "cargo_acc/serializers.py",
    # "static/js/load_product_table.js",
    # "static/js/client_cache.js",
    # "templates/cargo_acc/orders.html",
    # "templates/base.html",
    # "templates/cargo_acc/client_table.html",
    # "static/css/table.css",
    # "static/cargo_acc/js/client_table.js",
    # "templates/cargo_acc/mod_addrow.html",
    # "templates/cargo_acc/mod_delrow.html",
    # "templates/cargo_acc/settings_modal.html",
    # "requirements.txt",
    # "accounts/models.py",
    # "accounts/views.py",
    # Добавьте другие файлы по необходимости
]


def get_python_version():
    """Возвращает установленную версию Python."""
    return platform.python_version()


def get_installed_packages():
    """Возвращает список установленных пакетов."""
    try:
        result = subprocess.run(["pip", "freeze"], stdout=subprocess.PIPE, text=True)
        return result.stdout.splitlines()
    except Exception as e:
        return [f"Ошибка получения пакетов: {str(e)}"]


def build_tree(root, exclude_dirs, include_content):
    """Построение вложенного дерева проекта с учётом исключений и включения содержимого файлов."""
    tree = {"root": {}}

    def traverse(directory, current_level, rel_path=""):
        try:
            with os.scandir(directory) as entries:
                # Сортируем сначала папки, затем файлы, все в алфавитном порядке
                sorted_entries = sorted(entries, key=lambda e: (not e.is_dir(), e.name))
                for entry in sorted_entries:
                    entry_rel_path = f"{rel_path}/{entry.name}" if rel_path else entry.name

                    if entry.is_dir(follow_symlinks=False):
                        # Проверяем, исключена ли директория
                        is_excluded = any(
                            fnmatch.fnmatch(entry_rel_path, pattern) or fnmatch.fnmatch(entry.name, pattern)
                            for pattern in exclude_dirs
                        )
                        if is_excluded:
                            # Если папка исключена, добавляем её как пустую
                            current_level[entry.name] = {}
                        else:
                            # Если папка не исключена, рекурсивно обходим её содержимое
                            current_level[entry.name] = {}
                            traverse(entry.path, current_level[entry.name], entry_rel_path)

                    elif entry.is_file(follow_symlinks=False):
                        # Проверяем, включён ли файл в INCLUDE_CONTENT
                        if entry_rel_path in include_content:
                            # Читаем содержимое файла
                            content = get_file_content(entry.path)
                            current_level[entry.name] = {"content": content}
                        else:
                            # Просто добавляем файл без содержимого
                            current_level[entry.name] = {}

        except PermissionError:
            pass  # Игнорируем директории без доступа

    traverse(root, tree["root"])
    return tree


def get_file_content(file_path):
    """Читает содержимое файла."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        return f"Ошибка чтения файла: {str(e)}"


def analyze_project_structure(root, exclude_dirs, include_content):
    """Анализирует структуру проекта."""
    return {
        "Проект ПАРСЕР": "Новая задача - ответ давать максимально коротко! В ответе только то, что нужно добавить/удалить/заменить. Ни строки лишнего!!! В ответе  - только ответ на поставленный вопрос! Ни какой самодеятельности (типа это тоже ему пригодится). Отвечаем только на ПОСТАВЛЕННЫЙ ВОПРОС! Предоставляю выгрузку проекта. Это именно то что сейчас есть и работает и это все выгружено только что из проекта. Структура проекта и содержание файлов.",
        "python_version": get_python_version(),
        "pycharm": "PyCharm 2023.2.1 (Professional Edition)",
        "local project path": PROJECT_ROOT,
        "server project path": "/var/www/cargodb",
        "server venv": "/var/www/cargodb/venv/bin",
        "domain name": "https://bonablog.ru/",
        "requirements_content": get_file_content(os.path.join(root, "requirements.txt")),
        "tree": build_tree(root, exclude_dirs, include_content),
        "include_content": include_content,
        "ЗАДАЧА": "Задача"
    }


def write_structure_to_file(structure, output_file):
    """Записывает структуру проекта в файл в формате JSON."""
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(structure, file, ensure_ascii=False, indent=4)


def main():
    project_structure = analyze_project_structure(PROJECT_ROOT, EXCLUDED_DIRS, INCLUDE_CONTENT)
    write_structure_to_file(project_structure, OUTPUT_FILE)
    print(f"Project structure written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
