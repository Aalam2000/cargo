# accounts/services/client_actions.py
import json
import re
from typing import Dict, Any
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from accounts.models import CustomUser
from django.utils.crypto import get_random_string

import os
import threading
import requests
from django.db import transaction, IntegrityError
from cargo_acc.models import Client
from cargo_acc.services.code_generator import generate_client_code

import logging

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


def send_client_email_notification(
    *,
    email: str,
    notification_type: str,
    operator_user=None,
    password: str | None = None,
    client_code: str | None = None,
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

        link = f"{base_url}/login/"

        body = (

            "Здравствуйте!\n\n"

            "Для вас создана учетная запись в системе Cargo.\n\n"

            "Данные для входа:\n"

            f"Логин (email): {email}\n"

            f"Код клиента: {client_code}\n"

            f"Пароль: {password}\n\n"

            f"Ссылка для входа:\n{link}\n\n"

            "Рекомендуем сменить пароль после первого входа."

        )

    else:
        return  # неизвестный тип — молча выходим

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


def send_tg_message(chat_id: str, text: str) -> None:
    token = os.getenv("ADMIN_BOT_TG")
    if not token:
        logger.error("ADMIN_BOT_TG env variable is missing")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}

    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        logger.exception(f"Telegram send failed: {e}")


def _create_client_with_user_once(*, email: str, operator_user: CustomUser, name: str = "") -> str:
    """
    Одна попытка создания клиента/пользователя в транзакции.
    Внешняя функция делает retry при IntegrityError.
    """
    email = (email or "").strip()
    if not email:
        return "❗ E-mail пустой."

    with transaction.atomic():
        # 1) Пользователь существует?
        user = CustomUser.objects.filter(email__iexact=email).first()
        if user:
            send_client_email_notification(email=email, notification_type="invite_visit", operator_user=None)
            return f"✅ Клиент уже существует: {email}\n📩 Приглашение отправлено."

        # 2) Создаём нового пользователя (БЕЗ create_user)
        raw_password = get_random_string(12)

        user = CustomUser.objects.create(
            email=email,
            role="Client",
            company=operator_user.company,
            first_name=name or "",
            is_active=True,
        )

        user.set_password(raw_password)
        user.save(update_fields=["password"])

        # 3) Генерируем код клиента (атомарно, с блокировкой Company)
        client_code = generate_client_code(operator_user.company)

        # 4) Создаём клиента
        client = Client.objects.create(
            company=operator_user.company,
            client_code=client_code,
        )

        # 5) Привязываем
        user.linked_client = client
        user.client_code = client_code
        user.save(update_fields=["linked_client", "client_code"])

    # 6) Письмо новому (вне транзакции, чтобы не держать блокировки)
    send_client_email_notification(
        email=email,
        notification_type="invite_register",
        operator_user=None,
        password=raw_password,
        client_code=client_code,
    )

    return (
        "✅ Клиент создан\n"
        f"📧 Email: {email}\n"
        f"🆔 Код клиента: {client_code}\n"
        f"🔑 Пароль: {raw_password}\n"
        "📩 Данные отправлены клиенту на почту."
    )


def create_client_with_user(*, email: str, operator_user: CustomUser, name: str = "") -> str:
    """
    Создание клиента с защитным retry на случай гонок/параллельных путей создания.

    Критично: IntegrityError может прилететь не только по client_code,
    но и по другим UNIQUE (например, email). В этом случае повтор обычно
    безопасен: при повторе мы попадём в ветку "пользователь уже существует".
    """
    last_exc: Exception | None = None
    for attempt in range(1, 4):  # 1–3 попытки
        try:
            return _create_client_with_user_once(email=email, operator_user=operator_user, name=name)
        except IntegrityError as e:
            last_exc = e
            logger.warning(f"IntegrityError on create_client_with_user attempt={attempt}: {e}")
            continue

    logger.exception(f"create_client_with_user failed after retries: {last_exc}")
    return "❗ Не удалось создать клиента из-за конкурирующих операций. Попробуйте ещё раз."


def enqueue_create_client_action(*, telegram_id: str, operator_user_id: int, email: str, name: str = "", lang: str = "") -> None:
    def _job():
        try:
            operator_user = CustomUser.objects.get(id=operator_user_id)
            result = create_client_with_user(email=email, operator_user=operator_user, name=name)
            send_tg_message(telegram_id, result)
        except Exception as e:
            logger.exception(f"create_client job failed: {e}")
            send_tg_message(telegram_id, "❗ Ошибка при создании клиента. Смотрите police.log")

    t = threading.Thread(target=_job, daemon=True)
    t.start()
