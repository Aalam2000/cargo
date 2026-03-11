# accounts/services/company_actions.py
from __future__ import annotations

import logging
import re
import threading
from typing import Optional

from django.apps import apps
from django.db import IntegrityError, transaction
from django.utils.crypto import get_random_string

from accounts.models import CustomUser
from accounts.services.client_actions import send_tg_message

logger = logging.getLogger("pol")


def _clean(value: str | None) -> str:
    return (value or "").strip()


def _normalize_email(value: str | None) -> str:
    return _clean(value).lower()


def _is_valid_email(value: str | None) -> bool:
    email = _normalize_email(value)
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def build_create_company_preview(
    *,
    company_name: str,
    admin_email: str,
    admin_telegram: str = "",
    admin_name: str = "",
) -> str:
    parts = [
        "Будет выполнено действие: создание компании.",
        f"Компания: {company_name or '—'}",
        f"E-mail главного администратора: {admin_email or '—'}",
    ]
    if admin_telegram:
        parts.append(f"Telegram главного администратора: {admin_telegram}")
    if admin_name:
        parts.append(f"Имя главного администратора: {admin_name}")

    parts.append(
        "Алгоритм:\n"
        "• проверить, нет ли пользователя с таким e-mail;\n"
        "• проверить, нет ли компании с таким названием;\n"
        "• создать компанию;\n"
        "• создать главного администратора компании;\n"
        "• привязать пользователя к новой компании;\n"
        "• отправить результат в Telegram."
    )
    return "\n".join(parts)


def _create_company_with_admin_once(
    *,
    company_name: str,
    admin_email: str,
    operator_user: CustomUser,
    admin_telegram: str = "",
    admin_name: str = "",
) -> str:
    company_name = _clean(company_name)
    admin_email = _normalize_email(admin_email)
    admin_telegram = _clean(admin_telegram)
    admin_name = _clean(admin_name)

    if not company_name:
        return "❗ Не указано название компании."

    if not _is_valid_email(admin_email):
        return "❗ Некорректный e-mail главного администратора."

    Company = apps.get_model("cargo_acc", "Company")
    if Company is None:
        return "❗ Модель cargo_acc.Company не найдена."

    with transaction.atomic():
        existing_user = CustomUser.objects.filter(email__iexact=admin_email).first()
        if existing_user:
            return (
                "❗ Пользователь с таким e-mail уже существует.\n"
                f"📧 {admin_email}\n"
                "Создание компании остановлено."
            )

        existing_company = Company.objects.filter(name__iexact=company_name).first()
        if existing_company:
            return (
                "❗ Компания с таким названием уже существует.\n"
                f"🏢 {company_name}\n"
                "Создание остановлено."
            )

        company = Company.objects.create(
            name=company_name,
            registration="",
            description="",
            actual_address="",
            email=admin_email,
            legal_address="",
            ogrn="",
            phone="",
            representative_basis="",
            representative_fullname=admin_name,
            tax_id="",
        )

        raw_password = get_random_string(12)

        user = CustomUser.objects.create(
            email=admin_email,
            role="Admin",
            company=company,
            company_name=company_name,
            first_name=admin_name,
            telegram=admin_telegram,
            access_level="Company",
            assigned_object="",
            is_active=True,
            is_staff=False,
            is_superuser=False,
        )
        user.set_password(raw_password)
        user.save(update_fields=["password"])

    operator_company_id = getattr(operator_user, "company_id", None)

    return (
        "✅ Компания создана\n"
        f"🏢 Компания: {company_name}\n"
        f"🆔 Company ID: {company.id}\n"
        f"👤 Главный админ: {admin_email}\n"
        f"🧷 Telegram: {admin_telegram or '—'}\n"
        f"🔑 Пароль: {raw_password}\n"
        f"🔒 Изоляция данных: user.company_id = {company.id}\n"
        f"👨‍💼 Инициатор: operator.company_id = {operator_company_id}\n"
        "ℹ️ Новый пользователь будет видеть только данные своей компании."
    )


def create_company_with_admin(
    *,
    company_name: str,
    admin_email: str,
    operator_user: CustomUser,
    admin_telegram: str = "",
    admin_name: str = "",
) -> str:
    last_exc: Exception | None = None

    for attempt in range(1, 4):
        try:
            return _create_company_with_admin_once(
                company_name=company_name,
                admin_email=admin_email,
                operator_user=operator_user,
                admin_telegram=admin_telegram,
                admin_name=admin_name,
            )
        except IntegrityError as exc:
            last_exc = exc
            logger.warning("IntegrityError on create_company_with_admin attempt=%s: %s", attempt, exc)
            continue
        except Exception as exc:
            logger.exception("create_company_with_admin failed: %s", exc)
            return "❗ Ошибка при создании компании. Смотрите police.log"

    logger.exception("create_company_with_admin failed after retries: %s", last_exc)
    return "❗ Не удалось создать компанию из-за конкурирующих операций. Попробуйте ещё раз."


def enqueue_create_company_action(
    *,
    telegram_id: str,
    operator_user_id: int,
    company_name: str,
    admin_email: str,
    admin_telegram: str = "",
    admin_name: str = "",
) -> None:
    def _job():
        try:
            operator_user = CustomUser.objects.get(id=operator_user_id)
            result = create_company_with_admin(
                company_name=company_name,
                admin_email=admin_email,
                operator_user=operator_user,
                admin_telegram=admin_telegram,
                admin_name=admin_name,
            )
            send_tg_message(telegram_id, result)
        except Exception as exc:
            logger.exception("create_company job failed: %s", exc)
            send_tg_message(telegram_id, "❗ Ошибка при создании компании. Смотрите police.log")

    t = threading.Thread(target=_job, daemon=True)
    t.start()