import json
import os
import re
import threading
from typing import Dict, Any

import requests
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction, IntegrityError

from accounts.models import CustomUser
from cargo_acc.models import Client, SystemActionLog
from cargo_acc.services.code_generator import generate_client_code

import logging

logger = logging.getLogger("pol")

ADMIN_NOTIFY_CHAT_ID = (os.getenv("ADMIN_NOTIFY_TELEGRAM_CHAT_ID") or "").strip()


def build_client_action_preview(ai_json: str) -> str:
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

    parts = [
        "Будет выполнено действие: *создание/поиск клиента*.",
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
    if not ai_text:
        return {"action": "unknown", "email": "", "name": ""}

    cleaned = re.sub(r"```json|```", "", ai_text).strip()

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


def send_tg_message(chat_id: str, text: str) -> None:
    token = (
        os.getenv("TELEGRAM_BOT_TOKEN")
        or os.getenv("ADMIN_BOT_TG")
        or ""
    ).strip()

    if not token:
        logger.error("TELEGRAM_BOT_TOKEN / ADMIN_BOT_TG env variable is missing")
        return

    if not chat_id:
        logger.error("Telegram send failed: empty chat_id")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}

    try:
        response = requests.post(url, json=payload, timeout=10)
        response_text = response.text

        if response.status_code != 200:
            logger.error(
                "Telegram send failed: status=%s chat_id=%s response=%s",
                response.status_code,
                chat_id,
                response_text,
            )
            return

        try:
            data = response.json()
        except Exception:
            logger.error(
                "Telegram send failed: non-json response chat_id=%s response=%s",
                chat_id,
                response_text,
            )
            return

        if not data.get("ok"):
            logger.error(
                "Telegram send failed: chat_id=%s response=%s",
                chat_id,
                data,
            )
            return

        logger.info("Telegram sent successfully: chat_id=%s", chat_id)

    except Exception as e:
        logger.exception(f"Telegram send failed: {e}")


def _notify_admin_chat(text: str) -> None:
    if not ADMIN_NOTIFY_CHAT_ID:
        return
    send_tg_message(ADMIN_NOTIFY_CHAT_ID, text)


def _build_admin_action_message(
    *,
    action_name: str,
    request_telegram_id: str,
    email: str = "",
    name: str = "",
    company_name: str = "",
    result: str = "",
) -> str:
    parts = [
        f"🔔 Результат команды: {action_name}",
        f"👤 Инициатор TG: {request_telegram_id or '—'}",
    ]
    if company_name:
        parts.append(f"🏢 Компания: {company_name}")
    if email:
        parts.append(f"📧 Email: {email}")
    if name:
        parts.append(f"🙍 Имя: {name}")
    parts.append("")
    parts.append(result or "—")
    return "\n".join(parts)


def _log_bot_creation(*, operator_user: CustomUser, model_name: str, object_id: int, new_data: dict) -> None:
    try:
        SystemActionLog.objects.create(
            company=operator_user.company,
            model_name=model_name,
            object_id=object_id,
            action="create",
            diff={
                "source": "telegram_bot",
                "channel": "telegram",
                "created_from": "bot",
            },
            old_data=None,
            new_data=new_data,
            operator=operator_user,
        )
    except Exception as e:
        logger.exception(f"SystemActionLog create failed: {e}")


def _create_client_with_user_once(*, email: str, operator_user: CustomUser, name: str = "") -> str:
    email = (email or "").strip()
    if not email:
        return "❗ E-mail пустой."

    with transaction.atomic():
        user = CustomUser.objects.filter(email__iexact=email).first()
        if user:
            send_client_email_notification(
                email=email,
                notification_type="invite_visit",
                operator_user=None,
            )
            return (
                f"✅ Клиент уже существует: {email}\n"
                "📩 Приглашение отправлено."
            )

        raw_password = os.urandom(9).hex()

        user = CustomUser.objects.create(
            email=email,
            role="Client",
            company=operator_user.company,
            first_name=name or "",
            is_active=True,
        )
        user.set_password(raw_password)
        user.save(update_fields=["password"])

        client_code = generate_client_code(operator_user.company)

        client = Client.objects.create(
            company=operator_user.company,
            client_code=client_code,
            description="Создано из Telegram-бота Cargo",
        )

        user.linked_client = client
        user.client_code = client_code
        user.save(update_fields=["linked_client", "client_code"])

        _log_bot_creation(
            operator_user=operator_user,
            model_name="accounts.CustomUser",
            object_id=user.id,
            new_data={
                "email": user.email,
                "role": user.role,
                "client_code": user.client_code,
                "source": "telegram_bot",
            },
        )
        _log_bot_creation(
            operator_user=operator_user,
            model_name="cargo_acc.Client",
            object_id=client.id,
            new_data={
                "client_code": client.client_code,
                "description": client.description,
                "source": "telegram_bot",
            },
        )

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
        f"🏢 Компания: {operator_user.company.name}\n"
        "🤖 Источник: Telegram-бот Cargo\n"
        "📩 Данные отправлены клиенту на почту."
    )


def create_client_with_user(*, email: str, operator_user: CustomUser, name: str = "") -> str:
    last_exc: Exception | None = None
    for attempt in range(1, 4):
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

            send_tg_message(
                telegram_id,
                f"⏳ Начал создание клиента {email}"
            )

            result = create_client_with_user(email=email, operator_user=operator_user, name=name)

            send_tg_message(telegram_id, result)
            _notify_admin_chat(
                _build_admin_action_message(
                    action_name="create_client",
                    request_telegram_id=telegram_id,
                    email=email,
                    name=name,
                    company_name=getattr(operator_user.company, "name", ""),
                    result=result,
                )
            )
        except Exception as e:
            logger.exception(f"create_client job failed: {e}")
            error_text = "❗ Ошибка при создании клиента. Смотрите police.log"
            send_tg_message(telegram_id, error_text)
            _notify_admin_chat(
                _build_admin_action_message(
                    action_name="create_client",
                    request_telegram_id=telegram_id,
                    email=email,
                    name=name,
                    result=error_text,
                )
            )

    t = threading.Thread(target=_job, daemon=True)
    t.start()