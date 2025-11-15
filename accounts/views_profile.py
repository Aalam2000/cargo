import os
import io
import base64
import json
import qrcode
from django.conf import settings
from django.http import JsonResponse, HttpResponseForbidden, FileResponse, Http404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.crypto import get_random_string
from docxtpl import DocxTemplate

USER_DOCS_ROOT = os.path.join(settings.MEDIA_ROOT, "users")
TEMPLATE_PATH = os.path.join(settings.BASE_DIR, "web", "docs", "Договор_DD_Logistics.docx")


# === Проверки ролей ===
def is_admin(user):
    return user.is_authenticated and user.role == "Admin"


# === 1. Генерация договора клиентом ===
@login_required
def generate_contract(request):
    user = request.user
    if user.role != "Client" and not is_admin(user):
        return HttpResponseForbidden("Доступ запрещён")

    # если админ открывает чужой профиль
    username = request.GET.get("username") if is_admin(user) else user.username
    user_dir = os.path.join(USER_DOCS_ROOT, username)
    os.makedirs(user_dir, exist_ok=True)

    tpl = DocxTemplate(TEMPLATE_PATH)

    # === Формирование данных под договор ===

    # Общие параметры компании (наша сторона)
    context = {
        "day": "___",
        "month": "__________",
        "year": "2025",
        "company": {
            "name": "DD Logistics",
            "tax_id": "9900003611",
            "ogrn": "1303953611",
            "representative_fullname": "Тагиев Бахтияр Тельман оглы",
            "representative_basis": "Устава",
            "legal_address": "г. Баку, ул. Физули, 71",
            "actual_address": "г. Баку, ул. Физули, 71",
            "phone": "+994",
            "email": "info@ddlogistics.az",
        },
    }

    # === ЛОГИКА ДЛЯ ФИЗИЧЕСКОГО ЛИЦА ===
    if user.client_type == "individual":
        fullname = f"{user.last_name} {user.first_name}"

        context.update({
            "client_fullname": fullname,
            "client_inn_or_reg": user.inn,  # ИНН физика
            "client_representative": "",  # нет представителя
            "client_basis": "паспорта",  # фиксированное основание
            "client_company_name": fullname,  # в реквизитах — ФИО
            "client_address": user.address,  # адрес проживания
            "client_inn": user.inn,  # ИНН
            "client_ogrn": "",  # нет ОГРН
            "client_code": user.client_code,
        })

    # === ЛОГИКА ДЛЯ ЮР.ЛИЦА ===
    else:
        context.update({
            "client_fullname": user.company_name,  # название компании
            "client_inn_or_reg": user.inn,
            "client_representative": user.representative,
            "client_basis": user.basis,
            "client_company_name": user.company_name,
            "client_address": user.legal_address,  # юр. адрес
            "client_inn": user.inn,
            "client_ogrn": user.ogrn,
            "client_code": user.client_code,
        })

    tpl.render(context)

    filename = f"Договор_{username}.docx"
    filepath = os.path.join(user_dir, filename)
    tpl.save(filepath)

    file_url = settings.MEDIA_URL + f"users/{username}/{filename}"
    return JsonResponse({"url": file_url})


# === 2. Отправка e-mail ссылки для подписи ===
@login_required
def send_sign_link(request):
    user = request.user
    if user.role != "Client":
        return HttpResponseForbidden("Доступ запрещён")

    token = get_random_string(40)
    user.sign_token = token
    user.save()

    sign_url = request.build_absolute_uri(reverse("sign_contract", args=[token]))

    send_mail(
        subject="Подписание договора DD Logistics",
        message=f"Для подтверждения договора перейдите по ссылке:\n{sign_url}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    return JsonResponse({"status": "ok"})


# === 3. Подтверждение подписи ===
@login_required
def sign_contract(request, token):
    user = request.user
    if not hasattr(user, "sign_token") or user.sign_token != token:
        return HttpResponseForbidden("Неверный токен")

    user.contract_signed = True
    user.sign_token = None
    user.save()

    return JsonResponse({
        "status": "signed",
        "message": "Договор успешно подписан."
    })


# === 4. Генерация QR-оплаты ===
@login_required
def generate_qr_payment(request):
    user = request.user
    if user.role != "Client" and not is_admin(user):
        return HttpResponseForbidden("Доступ запрещён")

    username = request.GET.get("username") if is_admin(user) else user.username
    user_dir = os.path.join(USER_DOCS_ROOT, username)
    os.makedirs(user_dir, exist_ok=True)

    amount = 1000  # пример
    qr_data = f"PAYMENT|SBP|{username}|{amount}"

    img = qrcode.make(qr_data)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    qr_filename = f"qr_{username}.png"
    with open(os.path.join(user_dir, qr_filename), "wb") as f:
        f.write(buffer.getvalue())

    file_url = settings.MEDIA_URL + f"users/{username}/{qr_filename}"
    return JsonResponse({"qr_url": file_url})


# === 5. Просмотр файлов пользователя (доступно только админу) ===
@user_passes_test(is_admin)
def list_user_files(request, username):
    user_dir = os.path.join(USER_DOCS_ROOT, username)
    if not os.path.exists(user_dir):
        raise Http404("Папка пользователя не найдена")

    files = []
    for f in os.listdir(user_dir):
        path = os.path.join(user_dir, f)
        if os.path.isfile(path):
            files.append({
                "name": f,
                "url": settings.MEDIA_URL + f"users/{username}/{f}",
                "size_kb": round(os.path.getsize(path) / 1024, 1),
            })
    return JsonResponse({"files": files})


# === 6. Загрузка конкретного файла (админ или владелец) ===
@login_required
def download_user_file(request, username, filename):
    user = request.user
    if not (is_admin(user) or user.username == username):
        return HttpResponseForbidden("Доступ запрещён")

    file_path = os.path.join(USER_DOCS_ROOT, username, filename)
    if not os.path.exists(file_path):
        raise Http404("Файл не найден")

    return FileResponse(open(file_path, "rb"), as_attachment=True, filename=filename)
