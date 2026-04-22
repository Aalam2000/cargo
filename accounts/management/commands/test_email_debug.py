import os
import socket
import traceback

from django.conf import settings
from django.core.mail import EmailMessage, get_connection, send_mail
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Debug test for email sending with verbose print logging"

    def add_arguments(self, parser):
        parser.add_argument("--to", required=True, help="Recipient email")
        parser.add_argument(
            "--mode",
            default="raw",
            choices=["raw", "invite_visit", "invite_register"],
            help="Email body mode",
        )
        parser.add_argument(
            "--password",
            default="TEST_PASSWORD_123",
            help="Password for invite_register mode",
        )
        parser.add_argument(
            "--client-code",
            default="TEST001",
            help="Client code for invite_register mode",
        )
        parser.add_argument(
            "--subject",
            default="Cargo email debug test",
            help="Subject for raw mode",
        )

    def handle(self, *args, **options):
        to_email = (options.get("to") or "").strip()
        mode = (options.get("mode") or "raw").strip()
        password = (options.get("password") or "").strip()
        client_code = (options.get("client_code") or "").strip()
        raw_subject = (options.get("subject") or "").strip()

        print("=" * 80, flush=True)
        print("EMAIL DEBUG START", flush=True)
        print("=" * 80, flush=True)

        print("[STEP] Input params", flush=True)
        print(f"to_email={to_email}", flush=True)
        print(f"mode={mode}", flush=True)
        print(f"password={password}", flush=True)
        print(f"client_code={client_code}", flush=True)
        print(f"raw_subject={raw_subject}", flush=True)

        print("[STEP] Environment", flush=True)
        print(f"ENVIRONMENT={os.getenv('ENVIRONMENT', '')}", flush=True)
        print(f"DEBUG={os.getenv('DEBUG', '')}", flush=True)
        print(f"HOSTNAME={socket.gethostname()}", flush=True)

        print("[STEP] Django settings email-related", flush=True)
        email_setting_names = [
            "EMAIL_BACKEND",
            "EMAIL_HOST",
            "EMAIL_PORT",
            "EMAIL_HOST_USER",
            "EMAIL_HOST_PASSWORD",
            "EMAIL_USE_TLS",
            "EMAIL_USE_SSL",
            "EMAIL_TIMEOUT",
            "DEFAULT_FROM_EMAIL",
            "SERVER_EMAIL",
            "SITE_URL",
        ]

        for name in email_setting_names:
            value = getattr(settings, name, None)
            if name == "EMAIL_HOST_PASSWORD" and value:
                shown = "***MASKED***"
            else:
                shown = value
            print(f"{name}={shown}", flush=True)

        print("[STEP] Validation", flush=True)
        if not to_email:
            print("ERROR: --to is required", flush=True)
            return

        site_url = str(getattr(settings, "SITE_URL", "") or "").rstrip("/")
        default_from_email = str(getattr(settings, "DEFAULT_FROM_EMAIL", "") or "").strip()

        if not default_from_email:
            print("ERROR: DEFAULT_FROM_EMAIL is empty", flush=True)
            return

        print("[STEP] Build subject/body using project constants", flush=True)
        if mode == "invite_visit":
            subject = "Приглашение в личный кабинет"
            body = (
                "Здравствуйте!\n\n"
                "Вас приглашают посетить личный кабинет платформы Cargo.\n\n"
                f"Ссылка для входа:\n{site_url}/login/\n\n"
                "Если у вас возникнут вопросы — свяжитесь с вашим менеджером."
            )
        elif mode == "invite_register":
            subject = "Вы зарегистрированы в системе Cargo"
            body = (
                "Здравствуйте!\n\n"
                "Для вас создана учетная запись в системе Cargo.\n\n"
                "Данные для входа:\n"
                f"Логин (email): {to_email}\n"
                f"Код клиента: {client_code}\n"
                f"Пароль: {password}\n\n"
                f"Ссылка для входа:\n{site_url}/login/\n\n"
                "Рекомендуем сменить пароль после первого входа."
            )
        else:
            subject = raw_subject
            body = (
                "Это тестовое письмо Cargo.\n\n"
                f"SITE_URL: {site_url}\n"
                f"DEFAULT_FROM_EMAIL: {default_from_email}\n"
                f"EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', '')}\n"
                f"EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', '')}\n"
            )

        print(f"subject={subject}", flush=True)
        print("body=", flush=True)
        print(body, flush=True)

        print("[STEP] Open SMTP connection", flush=True)
        try:
            connection = get_connection(fail_silently=False)
            print(f"connection_class={connection.__class__.__name__}", flush=True)
            connection.open()
            print("SMTP connection opened successfully", flush=True)
        except Exception as exc:
            print("ERROR: connection.open() failed", flush=True)
            print(repr(exc), flush=True)
            print(traceback.format_exc(), flush=True)
            return
        finally:
            try:
                connection.close()
                print("SMTP connection closed", flush=True)
            except Exception as exc:
                print("WARN: connection.close() failed", flush=True)
                print(repr(exc), flush=True)

        print("[STEP] Send via send_mail()", flush=True)
        try:
            sent_count = send_mail(
                subject=subject,
                message=body,
                from_email=default_from_email,
                recipient_list=[to_email],
                fail_silently=False,
            )
            print(f"send_mail() result={sent_count}", flush=True)
        except Exception as exc:
            print("ERROR: send_mail() failed", flush=True)
            print(repr(exc), flush=True)
            print(traceback.format_exc(), flush=True)
            return

        print("[STEP] Send via EmailMessage()", flush=True)
        try:
            msg = EmailMessage(
                subject=subject,
                body=body,
                from_email=default_from_email,
                to=[to_email],
            )
            sent_count = msg.send(fail_silently=False)
            print(f"EmailMessage.send() result={sent_count}", flush=True)
        except Exception as exc:
            print("ERROR: EmailMessage.send() failed", flush=True)
            print(repr(exc), flush=True)
            print(traceback.format_exc(), flush=True)
            return

        print("=" * 80, flush=True)
        print("EMAIL DEBUG FINISHED OK", flush=True)
        print("=" * 80, flush=True)