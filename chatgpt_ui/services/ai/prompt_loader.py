import os
from django.conf import settings

_cache = None


def load_intent_prompt() -> str:
    global _cache
    if _cache:
        return _cache

    path = os.path.join(
        settings.BASE_DIR,
        "chatgpt_ui",
        "services",
        "ai",
        "prompts",
        "intent_detection.txt",
    )

    with open(path, "r", encoding="utf-8") as f:
        _cache = f.read()

    return _cache