# cargo_acc/views_payment.py
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.db.models import Q, F
from decimal import Decimal
from datetime import date
import json

import requests
from django.views.decorators.http import require_GET

from .models import Payment, PaymentProduct, Client, Product
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET", "POST", "PUT"])
@login_required
@transaction.atomic
def add_or_edit_payment(request):
    if request.method == "GET":
        pay_id = request.GET.get("id")
        payment = (
            Payment.objects.select_related("client", "company")
            .filter(id=pay_id)
            .first()
        )
        if not payment:
            return JsonResponse({"error": "Платёж не найден"}, status=404)

        return JsonResponse({
            "id": payment.id,
            "client_code": payment.client.client_code,
            "payment_date": payment.payment_date.isoformat(),
            "amount_total": float(payment.amount_total),
            "currency": payment.currency,
            "exchange_rate": float(payment.exchange_rate),
            "amount_usd": float(payment.amount_usd),
            "method": payment.method,
            "comment": payment.comment or "",
            "payment_type": payment.payment_type,
        })

    if request.method not in ["POST", "PUT"]:
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Некорректный JSON"}, status=400)

    user = request.user
    role = getattr(user, "role", "")
    if role not in ["Admin", "Operator"]:
        return JsonResponse({"error": "Нет прав на изменение"}, status=403)

    client_code = data.get("client_code")
    client = Client.objects.filter(client_code=client_code).first()
    if not client:
        return JsonResponse({"error": "Клиент не найден"}, status=400)

    payment_date = data.get("payment_date") or str(date.today())
    amount_total = Decimal(data.get("amount_total", 0))
    currency = data.get("currency", "RUB")
    exchange_rate = Decimal(data.get("exchange_rate", 1))
    comment = data.get("comment", "")
    method = data.get("method", "Наличные")
    payment_type = data.get("payment_type", "payment")

    if request.method == "PUT":
        pay_id = data.get("id")
        payment = Payment.objects.filter(id=pay_id).first()
        if not payment:
            return JsonResponse({"error": "Платёж не найден"}, status=404)

        payment.payment_date = payment_date
        payment.amount_total = amount_total
        payment.currency = currency
        payment.exchange_rate = exchange_rate
        payment.amount_usd = round(amount_total / exchange_rate, 2)
        payment.comment = comment
        payment.method = method
        payment.payment_type = payment_type

        payment.save(update_fields=[
            "payment_date", "amount_total", "currency", "exchange_rate",
            "amount_usd", "comment", "method", "payment_type"
        ])
        return JsonResponse({"ok": True, "payment_id": payment.id})

    # === POST ===
    payment = Payment.objects.create(
        company=client.company,
        client=client,
        payment_date=payment_date,
        amount_total=amount_total,
        currency=currency,
        exchange_rate=exchange_rate,
        amount_usd=round(amount_total / exchange_rate, 2),
        comment=comment,
        method=method,
        payment_type=payment_type,
        # created_by=user,
    )

    return JsonResponse({
        "ok": True,
        "payment_id": payment.id,
        "amount_usd": float(payment.amount_usd),
    })




@require_GET
@login_required
def get_currency_rate(request):
    """
    Возвращает курс валюты к USD, запрашивая Google Finance на сервере (без CORS)
    """
    cur = request.GET.get("currency", "RUB").upper()
    url = f"https://www.google.com/finance/quote/{cur}-USD"
    try:
        resp = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        html = resp.text
        import re
        m = re.search(r'>([0-9]+(?:\.[0-9]+)?)<', html)
        rate = float(m.group(1)) if m else 1.0
    except Exception as e:
        return JsonResponse({"error": str(e), "rate": 1.0})
    return JsonResponse({"currency": cur, "rate": rate})

