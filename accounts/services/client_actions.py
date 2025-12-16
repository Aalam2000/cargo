# accounts/services/client_actions.py
import json
import re
from typing import Dict, Any
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
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
        # найден существующий пользователь → приглашение войти
        send_client_email_notification(
            email=email,
            notification_type="invite_visit",
            operator_user=None,
        )

        return (
            "📧 Клиент найден.\n\n"
            f"E-mail: {email}\n"
            f"ID пользователя: {user.id}\n"
            f"Роль: {user.role}\n\n"
            "Клиенту отправлено письмо с приглашением "
            "в личный кабинет."
        )

    # пользователь не найден → письмо о регистрации
    send_client_email_notification(
        email=email,
        notification_type="invite_register",
        operator_user=None,
        password_reset_token=None,  # пока заглушка
    )

    return (
        "📧 Клиент не найден.\n\n"
        f"E-mail: {email}\n\n"
        "Пользователь будет создан на следующем шаге.\n"
        "Клиенту отправлено письмо о регистрации "
        "и необходимости авторизации в системе."
    )


def send_client_email_notification(
    *,
    email: str,
    notification_type: str,
    operator_user=None,
    password_reset_token: str | None = None,
) -> None:
    """
    Универсальная отправка e-mail клиенту.

    notification_type:
    - invite_visit
    - invite_register
    """

    base_url = settings.SITE_URL.rstrip("/")

    if notification_type == "invite_visit":
        subject = "Приглашение в личный кабинет"
        link = f"{base_url}/login/"
        body = (
            "Здравствуйте!\n\n"
            "Вас приглашают посетить личный кабинет платформы Cargo.\n\n"
            f"Ссылка для входа:\n{link}\n\n"
            "Если у вас возникнут вопросы — свяжитесь с вашим менеджером."
        )

    elif notification_type == "invite_register":
        subject = "Вы зарегистрированы в системе Cargo"
        reset_link = (
            f"{base_url}/set-password/{password_reset_token}/"
            if password_reset_token
            else f"{base_url}/login/"
        )
        body = (
            "Здравствуйте!\n\n"
            "Для вас создана учетная запись в системе Cargo.\n\n"
            "Пожалуйста:\n"
            "1. Задайте пароль;\n"
            "2. Заполните данные профиля;\n"
            "3. Подпишите договор-оферту.\n\n"
            f"Ссылка:\n{reset_link}\n\n"
            "После этого вы сможете отслеживать свои товары и доставки."
        )

    else:
        return  # неизвестный тип — молча выходим

    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
