# accounts/services/client_actions.py
import json
import re
from typing import Dict, Any

from accounts.models import CustomUser



def build_client_action_preview(ai_json: str) -> str:
    """
    Принимает JSON-строку от OpenAI и возвращает текст,
    который бот отправит оператору: что именно система
    собирается сделать.
    """
    try:
        data = safe_parse_ai_json(ai_json)
    except json.JSONDecodeError:
        return "❗ Команда не распознана: получен некорректный JSON от OpenAI."

    action = (data.get("action") or "").strip()
    email = (data.get("email") or "").strip()
    name = (data.get("name") or "").strip()

    if action != "create_client" or not email:
        return (
            "Команда не распознана или отсутствует e-mail.\n"
            "Никаких действий выполнено не будет."
        )

    # Базовое описание
    parts = [
        f"Будет выполнено действие: *создание/поиск клиента*.",
        f"E-mail: {email}.",
    ]
    if name:
        parts.append(f"Имя клиента: {name}.")

    parts.append(
        "Алгоритм:\n"
        "• найти пользователя с таким e-mail;\n"
        "• если найден — отправить приглашение и привязать к компании оператора;\n"
        "• если не найден — создать пользователя с ролью Клиент, "
        "создать карточку клиента и отправить приглашение."
    )

    return "\n".join(parts)


def safe_parse_ai_json(ai_text: str) -> Dict[str, Any]:
    """
    Гарантированно извлекает JSON из ответа OpenAI
    """
    if not ai_text:
        return {"action": "unknown", "email": "", "name": ""}

    # убираем ```json ``` и ```
    cleaned = re.sub(r"```json|```", "", ai_text).strip()

    # берём JSON между первой { и последней }
    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1 or end <= start:
        return {"action": "unknown", "email": "", "name": ""}

    json_text = cleaned[start: end + 1]

    try:
        return json.loads(json_text)
    except Exception:
        return {"action": "unknown", "email": "", "name": ""}



def preview_client_search(data: dict) -> str:
    """
    Отладочный поиск клиента по e-mail.
    НИЧЕГО не создаёт.
    """
    action = (data.get("action") or "").strip()
    email = (data.get("email") or "").strip()
    name = (data.get("name") or "").strip()

    if action != "create_client" or not email:
        return (
            "Команда не распознана или отсутствует e-mail.\n"
            "Поиск клиента не выполнялся."
        )

    user = CustomUser.objects.filter(email__iexact=email).first()

    if user:
        return (
            "🔍 Результат поиска клиента:\n"
            f"Пользователь с e-mail *{email}* НАЙДЕН.\n"
            f"ID пользователя: {user.id}\n"
            f"Роль: {user.role}\n\n"
            "На следующем шаге:\n"
            "• клиенту будет отправлено приглашение в систему."
        )

    return (
        "🔍 Результат поиска клиента:\n"
        f"Пользователь с e-mail *{email}* НЕ НАЙДЕН.\n\n"
        "На следующем шаге:\n"
        "• будет создан новый пользователь с ролью Клиент;\n"
        "• будет создана карточка клиента;\n"
        "• будет отправлено приглашение на e-mail."
    )
