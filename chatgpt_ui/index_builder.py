import os
import json
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def create_project_index():
    """Создаёт обновлённый индекс проекта."""
    project_index = {"structure": {}, "details": {}}

    # Анализ HTML файлов
    templates_dir = os.path.join(BASE_DIR, "web/templates")
    for root, _, files in os.walk(templates_dir):
        for file in files:
            if file.endswith(".html"):
                file_path = os.path.join(root, file)
                analyze_html(file_path, project_index)

    # Анализ JS файлов
    static_dir = os.path.join(BASE_DIR, "web/static/js")
    for root, _, files in os.walk(static_dir):
        for file in files:
            if file.endswith(".js"):
                file_path = os.path.join(root, file)
                analyze_js(file_path, project_index)

    # Сохранение индекса
    index_path = os.path.join(BASE_DIR, "tmp/project_index.json")
    with open(index_path, "w", encoding="utf-8") as index_file:
        json.dump(project_index, index_file, ensure_ascii=False, indent=4)

    print(f"Индекс проекта успешно создан: {index_path}")


def analyze_html(file_path, project_index):
    """Анализирует HTML файл и добавляет его в индекс."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        soup = BeautifulSoup(content, "html.parser")
        table_ids = [tag.get("id") for tag in soup.find_all("table", id=True)]
        scripts = [tag.get("src") for tag in soup.find_all("script", src=True)]

        relative_path = os.path.relpath(file_path, BASE_DIR)
        project_index["structure"].setdefault("templates", {})[relative_path] = {
            "type": "HTML",
            "description": f"HTML файл: {relative_path}",
            "linked_js": scripts,
            "id_elements": table_ids,
        }
        project_index["details"][relative_path] = {
            "excerpt": content[:200],
            "lines": len(content.splitlines()),
        }
    except Exception as e:
        print(f"Ошибка при анализе HTML {file_path}: {e}")


def analyze_js(file_path, project_index):
    """Анализирует JS файл и добавляет его в индекс."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        # Находим функции
        function_pattern = r'function\s+(\w+)\s*\(.*?\)\s*{'
        functions = re.findall(function_pattern, content)

        # Ищем связанные элементы
        related_elements = []
        table_pattern = r'\b(product-table.*?)\b'
        related_elements.extend(re.findall(table_pattern, content))

        relative_path = os.path.relpath(file_path, BASE_DIR)
        project_index["structure"].setdefault("static/js", {})[relative_path] = {
            "type": "JS",
            "description": f"JS файл: {relative_path}",
            "functions": functions,
            "related_elements": related_elements,
        }
        project_index["details"][relative_path] = {
            "excerpt": content[:200],
            "lines": len(content.splitlines()),
        }
    except Exception as e:
        print(f"Ошибка при анализе JS {file_path}: {e}")


if __name__ == "__main__":
    create_project_index()
