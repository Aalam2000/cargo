# accounts/services/client_actions.py
import json
import logging
import re
from typing import Dict, Any

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils.crypto import get_random_string

logger = logging.getLogger("tg_bot")

from .client_actions import send_client_email_notification

logger = logging.getLogger("pol")


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


@transaction.atomic
def create_client_with_user(*, email, operator_user, name=""):
    logger.info("=== CREATE CLIENT START ===")
    logger.info(f"Email={email}, Operator={operator_user.id}")

    email = email.strip().lower()

    from accounts.models import CustomUser
    from cargo_acc.models import Client
    from cargo_acc.services.code_generator import generate_client_code

    user = CustomUser.objects.filter(email__iexact=email).first()

    if user:
        logger.info(f"User EXISTS id={user.id}")
        send_client_email_notification(
            email=email,
            notification_type="invite_visit",
            operator_user=operator_user,
        )
        logger.info("Invite_visit email sent")
        return f"Клиент уже существует. Приглашение отправлено: {email}"

    logger.info("User NOT found → creating")

    password = get_random_string(10)

    user = CustomUser.objects.create_user(
        email=email,
        password=password,
        role="Client",
        company=operator_user.company,
        first_name=name or "",
        is_active=True,
    )
    logger.info(f"User created id={user.id}")

    client_code = generate_client_code(operator_user.company)
    logger.info(f"Generated client_code={client_code}")

    client = Client.objects.create(
        client_code=client_code,
        company=operator_user.company,
    )
    logger.info(f"Client created id={client.id}")

    user.linked_client = client
    user.client_code = client_code
    user.save(update_fields=["linked_client", "client_code"])
    logger.info("User linked to client")

    send_client_email_notification(
        email=email,
        notification_type="invite_register",
        operator_user=operator_user,
    )
    logger.info("Invite_register email sent")

    return f"Клиент создан: {email}, код {client_code}"


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
    email = (email or "").strip()
    if not email:
        return

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
        return

    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception as e:
        logger.exception(f"EMAIL SEND ERROR to {email}: {e}")
