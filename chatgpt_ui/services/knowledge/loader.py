import os
from django.conf import settings

_cache = {}


def _read_file(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_help_pages() -> dict:
    global _cache

    if _cache:
        return _cache

    base = os.path.join(settings.BASE_DIR, "web", "templates", "chatgpt_ui")

    bot_help = _read_file(os.path.join(base, "bot_help.html"))
    platform_help = _read_file(os.path.join(base, "platform_help.html"))

    _cache = {
        "bot_help": bot_help,
        "platform_help": platform_help,
    }

    return _cache