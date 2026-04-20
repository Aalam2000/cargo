# chatgpt_ui/services/ai/prompt_loader.py
from __future__ import annotations

from pathlib import Path

from django.conf import settings


PROMPTS_DIR = Path(settings.BASE_DIR) / "chatgpt_ui" / "services" / "ai" / "prompts"


def load_prompt(filename: str) -> str:
    path = PROMPTS_DIR / filename
    return path.read_text(encoding="utf-8").strip()