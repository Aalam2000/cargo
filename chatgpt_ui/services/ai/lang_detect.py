# chatgpt_ui/services/ai/lang_detect.py
import os
from openai import OpenAI

_client = None


def _get_client():
    global _client
    if _client:
        return _client

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    _client = OpenAI(api_key=api_key)
    return _client


def detect_language(text: str, fallback: str = "en") -> str:
    text = (text or "").strip()
    if not text:
        return fallback

    client = _get_client()
    if not client:
        return fallback

    prompt = (
        "Detect language. Return ONLY code: "
        "ru, en, az, tr, zh-hans, zh-hant, zh-hk.\n\n"
        f"{text}"
    )

    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        lang = (r.choices[0].message.content or "").strip().lower()

        allowed = {"ru", "en", "az", "tr", "zh-hans", "zh-hant", "zh-hk"}
        return lang if lang in allowed else fallback

    except Exception:
        return fallback