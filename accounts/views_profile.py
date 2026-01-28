# accounts/views_profile.py
from datetime import datetime
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
from accounts.models import CustomUser
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
from django.http import HttpResponse
from django.views.decorators.clickjacking import xframe_options_sameorigin
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from weasyprint import HTML
from django.views.decorators.clickjacking import xframe_options_exempt


USER_DOCS_ROOT = os.path.join(settings.MEDIA_ROOT, "users")
TEMPLATE_PATH = os.path.join(settings.BASE_DIR, "web", "docs", "Договор_DD_Logistics.docx")
HTML_TEMPLATE_PATH = os.path.join(settings.BASE_DIR, "web", "docs", "_DD_Logistics.html")


# === Проверки ролей ===
def is_admin(user):
    return user.is_authenticated and user.role == "Admin"


# === 1. Генерация договора клиентом ===
@login_required
@xframe_options_exempt
def generate_contract(request):
    user = request.user

    if user.role != "Client" and not is_admin(user):
        return JsonResponse({"error": "Договор доступен только клиенту"}, status=403)

    # Для админа можно смотреть договор по client_code
    if is_admin(user):
        client_code = request.GET.get("client_code") or request.GET.get("username")
        if not client_code:
            return JsonResponse({"error": "client_code (или username) обязателен для администратора"}, status=400)

        try:
            contract_user = CustomUser.objects.get(client_code=client_code)
        except CustomUser.DoesNotExist:
            return JsonResponse({"error": f"Клиент с кодом {client_code} не найден"}, status=404)
    else:
        client_code = user.client_code
        contract_user = user

    if not client_code:
        return JsonResponse({"error": "У клиента не задан client_code"}, status=400)

    # -----------------------
    # PDF из web/docs/_DD_Logistics.html (Jinja2) -> inline
    # -----------------------
    html_path = HTML_TEMPLATE_PATH
    html_dir = os.path.dirname(html_path)
    html_name = os.path.basename(html_path)

    if not os.path.exists(html_path):
        return JsonResponse({"error": f"Не найден шаблон HTML: {html_path}"}, status=500)

    now = datetime.now()
    client_fullname = f"{getattr(contract_user, 'first_name', '')} {getattr(contract_user, 'last_name', '')}".strip()

    # company.* — в шаблоне используется как объект
    company_ctx = {
        "name": getattr(contract_user, "company_name", "") or client_fullname,
        "tax_id": getattr(contract_user, "inn", "") or "",
        "ogrn": getattr(contract_user, "ogrn", "") or "",
        "legal_address": (getattr(contract_user, "legal_address", "") or getattr(contract_user, "address", "") or ""),
        "actual_address": getattr(contract_user, "actual_address", "") or "",
        "representative_fullname": getattr(contract_user, "representative", "") or client_fullname,
        "representative_basis": getattr(contract_user, "basis", "") or "",
        "email": getattr(contract_user, "email", "") or "",
        "phone": getattr(contract_user, "phone", "") or "",
    }

    # client_* + day/month/year — как в твоём _DD_Logistics.html
    ctx = {
        "client_code": client_code,
        "client_fullname": client_fullname,
        "client_company_name": getattr(contract_user, "company_name", "") or client_fullname,
        "client_inn": getattr(contract_user, "inn", "") or "",
        "client_ogrn": getattr(contract_user, "ogrn", "") or "",
        "client_address": (getattr(contract_user, "legal_address", "") or getattr(contract_user, "address", "") or ""),
        "client_representative": getattr(contract_user, "representative", "") or client_fullname,
        "client_basis": getattr(contract_user, "basis", "") or "",
        "client_inn_or_reg": getattr(contract_user, "inn", "") or "",
        "day": f"{now.day:02d}",
        "month": f"{now.month:02d}",
        "year": f"{now.year}",
    }

    env = Environment(
        loader=FileSystemLoader(html_dir),
        undefined=StrictUndefined,
        autoescape=True,
    )
    template = env.get_template(html_name)

    html_rendered = template.render(company=company_ctx, **ctx)

    base_url = f"file://{os.path.join(settings.BASE_DIR, 'web')}"
    pdf_bytes = HTML(string=html_rendered, base_url=base_url).write_pdf()

    pdf_filename = f"Договор_{client_code}.pdf"

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{pdf_filename}"'

    # У тебя глобально X_FRAME_OPTIONS = DENY, поэтому:
    response["X-Frame-Options"] = "SAMEORIGIN"
    return response


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

    username = request.GET.get("username") if is_admin(user) else user.client_code
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
    if not (is_admin(user) or user.client_code == username):
        return HttpResponseForbidden("Доступ запрещён")

    file_path = os.path.join(USER_DOCS_ROOT, username, filename)
    if not os.path.exists(file_path):
        raise Http404("Файл не найден")

    return FileResponse(open(file_path, "rb"), as_attachment=True, filename=filename)
