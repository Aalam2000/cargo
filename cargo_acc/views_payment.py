from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db import transaction
from decimal import Decimal
from datetime import date
import json

from .models import Payment, PaymentProduct, Client, Product

@csrf_exempt
@transaction.atomic
def add_or_edit_payment(request):
    """
    POST: добавление новой оплаты
    PUT: редактирование существующей
    """
    if request.method not in ["POST", "PUT"]:
        return JsonResponse({"error": "Method not allowed"}, status=405)

    data = json.loads(request.body.decode("utf-8"))
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
        payment.updated_by = user
        payment.save(update_fields=[
            "payment_date", "amount_total", "currency",
            "exchange_rate", "amount_usd", "comment", "method", "updated_by"
        ])
        return JsonResponse({"ok": True, "payment_id": payment.id})

    # --- Новый платёж ---
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
        created_by=user,
        updated_by=user,
    )

    # --- Привязка к неоплаченным товарам ---
    remaining = amount_total
    unpaid_products = (
        Product.objects.filter(client=client)
        .exclude(payment_links__isnull=False)
        .order_by("shipping_date")
    )
    for p in unpaid_products:
        if remaining <= 0:
            break
        pay_amount = min(remaining, p.cost or 0)
        if pay_amount > 0:
            PaymentProduct.objects.create(
                payment=payment,
                product=p,
                company=p.company,
                allocated_amount=pay_amount,
            )
            remaining -= pay_amount

    return JsonResponse({
        "ok": True,
        "payment_id": payment.id,
        "remaining_as_advance": float(remaining),
        "amount_usd": float(payment.amount_usd),
    })
