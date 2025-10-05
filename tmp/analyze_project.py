import os
import json
from pathlib import Path

# === Настройки ===
BASE_DIR = Path(__file__).resolve().parent.parent   # корень проекта (на 1 уровень выше tmp)
TMP_DIR = Path(__file__).resolve().parent            # папка tmp
OUTPUT_FILE = TMP_DIR / "project_analysis.json"      # результат
GITIGNORE_FILE = BASE_DIR / ".gitignore"
REQUIREMENTS_FILE = BASE_DIR / "requirements.txt"


def load_gitignore_patterns():
    """Считывает .gitignore и возвращает список шаблонов."""
    patterns = []
    if GITIGNORE_FILE.exists():
        with open(GITIGNORE_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                patterns.append(line)
    return patterns


def is_ignored(path, patterns):
    """Проверяет, попадает ли путь под исключение из .gitignore."""
    from fnmatch import fnmatch
    for p in patterns:
        # поддержка шаблонов типа *.pyc, /tmp/, build/
        if fnmatch(str(path), p) or fnmatch(path.name, p):
            return True
        # поддержка каталогов (например, "tmp/")
        if path.is_dir() and (p.rstrip("/") == path.name or fnmatch(str(path), p.rstrip("/"))):
            return True
    return False


def build_tree(root, patterns):
    """Рекурсивно строит структуру проекта, исключая gitignore."""
    tree = {}
    for item in sorted(root.iterdir()):
        if item.name.startswith("."):
            continue  # скрытые файлы (вроде .git, .idea и т.п.)
        if is_ignored(item, patterns):
            continue
        if item.is_dir():
            tree[item.name] = build_tree(item, patterns)
        else:
            tree[item.name] = None
    return tree


def read_file(path):
    """Считывает текст из файла или возвращает '' если файла нет."""
    if path.exists():
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    return ""


def main():
    patterns = load_gitignore_patterns()
    tree = build_tree(BASE_DIR, patterns)

    data = {
        "gitignore_content": read_file(GITIGNORE_FILE),
        "requirements_content": read_file(REQUIREMENTS_FILE),
        "project_structure": tree,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Анализ завершён. Результат сохранён в: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
