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
    # print("▶️ [add_or_edit_payment] START:", request.method)

    if request.method == "GET":
        pay_id = request.GET.get("id")
        # print("🟦 GET id:", pay_id)
        payment = (
            Payment.objects.select_related("client", "cargo", "company")
            .filter(id=pay_id)
            .first()
        )
        if not payment:
            # print("❌ GET: Платёж не найден")
            return JsonResponse({"error": "Платёж не найден"}, status=404)

        # print("✅ GET: найден платёж", payment.id)
        return JsonResponse({
            "id": payment.id,
            "client_code": payment.client.client_code,
            "cargo_code": getattr(payment.cargo, "cargo_code", ""),
            "payment_date": payment.payment_date.isoformat(),
            "amount_total": float(payment.amount_total),
            "currency": payment.currency,
            "exchange_rate": float(payment.exchange_rate),
            "amount_usd": float(payment.amount_usd),
            "method": payment.method,
            "comment": payment.comment or "",
            # "created_by": getattr(payment.created_by, "username", ""),
        })

    # === POST / PUT ===
    if request.method not in ["POST", "PUT"]:
        # print("⚠️ Method not allowed:", request.method)
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        # print("📩 JSON data:", data)
    except Exception as e:
        # print("❌ JSON parse error:", e)
        return JsonResponse({"error": "Некорректный JSON"}, status=400)

    user = request.user
    role = getattr(user, "role", "")
    # print("👤 user:", user.username, "| role:", role)

    if role not in ["Admin", "Operator"]:
        # print("🚫 Нет прав на изменение:", role)
        return JsonResponse({"error": "Нет прав на изменение"}, status=403)

    client_code = data.get("client_code")
    client = Client.objects.filter(client_code=client_code).first()
    # print("🟨 client_code:", client_code, "| client:", client)
    if not client:
        # print("❌ Клиент не найден")
        return JsonResponse({"error": "Клиент не найден"}, status=400)

    payment_date = data.get("payment_date") or str(date.today())
    amount_total = Decimal(data.get("amount_total", 0))
    currency = data.get("currency", "RUB")
    exchange_rate = Decimal(data.get("exchange_rate", 1))
    comment = data.get("comment", "")
    method = data.get("method", "Наличные")
    cargo_code = data.get("cargo_code")

    # print(f"💰 Data parsed | date={payment_date} amount={amount_total} currency={currency} rate={exchange_rate} method={method}")

    # === PUT ===
    if request.method == "PUT":
        pay_id = data.get("id")
        # print("🟩 PUT id:", pay_id)
        payment = Payment.objects.filter(id=pay_id).first()
        if not payment:
            # print("❌ PUT: не найден платёж")
            return JsonResponse({"error": "Платёж не найден"}, status=404)

        cargo = None
        if cargo_code:
            cargo = Product.objects.filter(product_code=cargo_code, client=client).first()
            # print("⚙️ PUT cargo:", cargo)
            if cargo:
                payment.cargo = cargo

        payment.payment_date = payment_date
        payment.amount_total = amount_total
        payment.currency = currency
        payment.exchange_rate = exchange_rate
        payment.amount_usd = round(amount_total / exchange_rate, 2)
        payment.comment = comment
        payment.method = method

        try:
            payment.save(update_fields=[
                "cargo", "payment_date", "amount_total", "currency",
                "exchange_rate", "amount_usd", "comment", "method"
            ])
            # print("✅ PUT: сохранено")
        except Exception as e:
            # print("❌ PUT save error:", e)
            raise
        return JsonResponse({"ok": True, "payment_id": payment.id})

    # === POST ===
    # print("🟦 POST создание платежа...")
    cargo = None
    if cargo_code:
        cargo = Product.objects.filter(product_code=cargo_code, client=client).first()
    # print("⚙️ cargo:", cargo)

    try:
        payment = Payment.objects.create(
            company=client.company,
            client=client,
            cargo=cargo,
            payment_date=payment_date,
            amount_total=amount_total,
            currency=currency,
            exchange_rate=exchange_rate,
            amount_usd=round(amount_total / exchange_rate, 2),
            comment=comment,
            method=method,
            # created_by=user,
        )
        # print("✅ Payment создан:", payment.id)
    except Exception as e:
        # print("❌ Ошибка при создании Payment:", e)
        raise

    remaining = amount_total
    unpaid_products = (
        Product.objects.filter(client=client)
        .exclude(payment_links__isnull=False)
        .order_by("shipping_date")
    )
    # print("📦 unpaid_products:", unpaid_products.count())

    for p in unpaid_products:
        if remaining <= 0:
            break
        pay_amount = min(remaining, p.cost or 0)
        if pay_amount > 0:
            try:
                PaymentProduct.objects.create(
                    payment=payment,
                    product=p,
                    company=p.company,
                    allocated_amount=pay_amount,
                )
                # print(f"🔗 Привязка {p.product_code}: {pay_amount}")
                remaining -= pay_amount
            except Exception as e:
                # print("❌ Ошибка при создании PaymentProduct:", e)
                raise

    # print("✅ Завершено успешно | remaining:", remaining)
    return JsonResponse({
        "ok": True,
        "payment_id": payment.id,
        "remaining_as_advance": float(remaining),
        "amount_usd": float(payment.amount_usd),
    })


@login_required
def get_unpaid_cargos(request):
    """Возвращает все неоплаченные или частично оплаченные грузы клиента."""
    code = request.GET.get("client_code", "").strip()
    client = Client.objects.filter(client_code=code).first()
    if not client:
        return JsonResponse({"results": []})

    unpaid = Product.objects.filter(client=client).filter(
        Q(payment_links__isnull=True) | Q(payment_links__allocated_amount__lt=F("cost"))
    ).order_by("shipping_date")

    results = [{"id": p.id, "product_code": p.product_code, "cost": float(p.cost or 0)} for p in unpaid]
    return JsonResponse({"results": results})


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

