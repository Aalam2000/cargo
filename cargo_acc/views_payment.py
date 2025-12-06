# cargo_acc/views_payment.py
import json
from datetime import date
from decimal import Decimal
from cargo_acc.company_utils import get_user_company
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_http_methods
from django.db.models import Case, When, Value, CharField
from django.http import JsonResponse
from cargo_acc.models import Payment, Client
from django.forms.models import model_to_dict
import logging

logger = logging.getLogger("pol")


@require_http_methods(["GET", "POST", "PUT"])
@login_required
@transaction.atomic
def add_or_edit_payment(request):
    from cargo_acc.models import (
        Payment,
        Client,
        PaymentType,
        AccrualType,
    )

    # ============================
    # GET (получение документа)
    # ============================
    if request.method == "GET":
        pay_id = request.GET.get("id")
        company = get_user_company(request)
        p = Payment.objects.filter(id=pay_id, company=company).first()
        if not p:
            return JsonResponse({"error": "Платёж не найден"}, status=404)

        return JsonResponse({
            "id": p.id,
            "client_code": p.client.client_code,
            "payment_date": p.payment_date.isoformat(),
            "amount_total": float(abs(p.amount_total)),
            "is_accrual": p.amount_total > 0,
            "operation_kind": p.operation_kind,
            "operation_type_id": (
                p.payment_type_id if p.operation_kind == 1 else p.accrual_type_id
            ),
            "operation_type_name": (
                p.payment_type.name if p.operation_kind == 1 and p.payment_type else
                p.accrual_type.name if p.operation_kind == 2 and p.accrual_type else
                ""
            ),
            "currency": p.currency,
            "exchange_rate": float(p.exchange_rate),
            "amount_usd": float(abs(p.amount_usd)),
            "method": p.method,
            "comment": p.comment or "",
            "products": p.products or [],
            "cargos": p.cargos or [],
        })

    # ============================
    # POST / PUT (создание/редактирование)
    # ============================

    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Некорректный JSON"}, status=400)

    user = request.user
    if user.role not in ["Admin", "Operator"]:
        return JsonResponse({"error": "Нет прав"}, status=403)

    # --- Клиент ---
    client_code = data.get("client_code")
    company = get_user_company(request)
    client = Client.objects.filter(client_code=client_code, company=company).first()
    if not client:
        return JsonResponse({"error": "Клиент не найден"}, status=400)

    # --- Основные поля ---
    payment_date = data.get("payment_date") or str(date.today())

    # ❗ Запрет ввода отрицательных значений и знаков +/-
    clean_amount = str(data.get("amount_total", "0")).replace("+", "").replace("-", "")
    raw_amount = Decimal(clean_amount or "0")

    currency = data.get("currency", "RUB")
    exchange_rate = Decimal(str(data.get("exchange_rate", 1)))
    comment = data.get("comment", "")
    method = data.get("method", "bank")

    # --- Тип операции: 1=оплата, 2=начисление ---
    operation_kind = int(data.get("payment_type"))

    # --- Вид операции ---
    operation_type_id = data.get("operation_type_id")

    if operation_kind == 1:  # Оплата
        operation_type = PaymentType.objects.filter(id=operation_type_id).first()
        if not operation_type:
            return JsonResponse({"error": "Некорректный вид оплаты"}, status=400)
        signed_amount = -abs(raw_amount)

    else:  # Начисление
        operation_type = AccrualType.objects.filter(id=operation_type_id).first()
        if not operation_type:
            return JsonResponse({"error": "Некорректный вид начисления"}, status=400)
        signed_amount = abs(raw_amount)

    products = data.get("products", [])
    cargos = data.get("cargos", [])

    # ============================
    # UPDATE (PUT)
    # ============================
    if request.method == "PUT":
        pay_id = data.get("id")
        company = get_user_company(request)
        p = Payment.objects.filter(id=pay_id, company=company).first()
        if not p:
            return JsonResponse({"error": "Платёж не найден"}, status=404)

        # ❗ НЕЛЬЗЯ менять клиента
        if p.client.client_code != client_code:
            return JsonResponse({"error": "Нельзя менять клиента у существующей операции"}, status=400)

        # ❗ НЕЛЬЗЯ менять тип операции (Оплата/Начисление)
        if p.operation_kind != operation_kind:
            return JsonResponse({"error": "Нельзя менять тип операции (Оплата/Начисление) при редактировании"},
                                status=400)

        # ❗ НЕЛЬЗЯ менять вид операции (PaymentType / AccrualType)
        old_type_id = p.payment_type_id if p.operation_kind == 1 else p.accrual_type_id
        if str(old_type_id) != str(operation_type_id):
            return JsonResponse({"error": "Нельзя менять вид операции при редактировании"}, status=400)

        # --- ОБНОВЛЕНИЕ ДОПУСТИМЫХ ПОЛЕЙ ---
        p.payment_date = payment_date
        p.amount_total = signed_amount
        p.currency = currency
        p.exchange_rate = exchange_rate

        # ❗ Пересчёт строго на стороне сервера
        p.amount_usd = round(abs(signed_amount) / exchange_rate, 2)

        p.method = method
        p.comment = comment
        p.products = products
        p.cargos = cargos

        p.save()
        return JsonResponse({"ok": True, "id": p.id})

    # ============================
    # CREATE (POST)
    # ============================

    p = Payment.objects.create(
        company=client.company,
        client=client,
        payment_date=payment_date,
        amount_total=signed_amount,
        currency=currency,
        exchange_rate=exchange_rate,
        amount_usd=round(abs(signed_amount) / exchange_rate, 2),
        operation_kind=operation_kind,
        payment_type=operation_type if operation_kind == 1 else None,
        accrual_type=operation_type if operation_kind == 2 else None,
        method=method,
        comment=comment,
        products=products,
        cargos=cargos,
        created_by=user,
    )

    return JsonResponse({
        "ok": True,
        "id": p.id,
        "amount_usd": float(abs(p.amount_usd)),
    })


@require_GET
@login_required
def get_currency_rate(request):
    """
    Возвращает курс 1 USD = X <валюта> на указанную дату
    из внутренней таблицы CurrencyRate.
    Если на указанную дату нет курса — берётся последний предыдущий.
    Если есть custom_rate — используется он.
    """
    from datetime import datetime
    from cargo_acc.models import CurrencyRate

    cur = request.GET.get("currency", "RUB").upper().strip()
    date_str = request.GET.get("date") or datetime.utcnow().strftime("%Y-%m-%d")
    date = datetime.strptime(date_str, "%Y-%m-%d").date()

    print("────────────────────────────────────────────", flush=True)
    print(f"[get_currency_rate] ▶ Локальный запрос: currency={cur}, date={date}", flush=True)

    if cur == "USD":
        return JsonResponse({
            "currency": "USD",
            "base": "USD",
            "rate": 1.0,
            "source": "local",
            "date": date_str,
        })

    # 1) сначала ищем курс на дату или раньше
    rate_obj = (
        CurrencyRate.objects.filter(currency=cur, date__lte=date)
        .order_by("-date")
        .first()
    )

    # 2) если нет — берём последний доступный курс вообще
    if not rate_obj:
        rate_obj = (
            CurrencyRate.objects.filter(currency=cur)
            .order_by("-date")
            .first()
        )

    # 3) если вообще нет ни одного курса
    if not rate_obj:
        return JsonResponse({"error": f"Нет данных по валюте {cur}"}, status=404)

    if not rate_obj:
        return JsonResponse({"error": f"Нет данных по валюте {cur}"}, status=404)

    # Приоритет: custom_rate > rate*(1+conversion_percent/100) > rate
    if rate_obj.custom_rate:
        rate = rate_obj.custom_rate
        source = "custom_rate"
    elif rate_obj.conversion_percent:
        rate = rate_obj.rate * (1 + rate_obj.conversion_percent / 100)
        source = f"rate+{rate_obj.conversion_percent}%"
    else:
        rate = rate_obj.rate
        source = "official_rate"

    return JsonResponse({
        "currency": cur,
        "base": "USD",
        "rate": float(rate),
        "source": source,
        "date": rate_obj.date.strftime("%Y-%m-%d"),
    })


# ================================
#  API: Баланс клиента
# ================================


@login_required
def client_balance(request):
    user = request.user
    role = getattr(user, "role", "")

    # --- 1. Определяем клиента ---
    if role == "Client":
        linked = getattr(user, "linked_client", None)
        if not linked:
            return JsonResponse({
                "total_paid": 0,
                "last_payment_date": "",
                "last_payment_amount": 0
            })
        client = linked

    elif role in ("Admin", "Operator"):
        code = request.GET.get("client_code", "").strip()
        if not code:
            return JsonResponse({
                "total_paid": 0,
                "last_payment_date": "",
                "last_payment_amount": 0
            })

        company = get_user_company(request)
        client = Client.objects.filter(client_code__icontains=code, company=company).first()
        if not client:

            return JsonResponse({
                "total_paid": 0,
                "last_payment_date": "",
                "last_payment_amount": 0
            })



    else:
        return JsonResponse({"error": "forbidden"}, status=403)

    # --- 2. BALANCE + LAST PAYMENT + USER INFO ---
    payments = Payment.objects.filter(client=client, company=client.company).order_by("-payment_date", "-id")

    balance = sum(p.amount_usd for p in payments)

    last_payment = (
        Payment.objects.filter(client=client, company=client.company, operation_kind=1)
        .order_by("-payment_date", "-id")
        .first()
    )

    last_payment_date = last_payment.payment_date.strftime("%d.%m.%Y") if last_payment else ""
    last_payment_amount = float(last_payment.amount_total) if last_payment else 0

    from accounts.models import CustomUser
    user_obj = CustomUser.objects.filter(linked_client=client).first()
    user_name = f"{user_obj.first_name} {user_obj.last_name}".strip() if user_obj else ""

    return JsonResponse({
        "balance": float(balance),
        "last_payment_date": last_payment_date,
        "last_payment_amount": last_payment_amount,
        "user_name": user_name,
        "client_code": client.client_code,
    })


# =============================================
#        API: ПЛАТЕЖИ (АНАЛОГ products_table)
# =============================================
@login_required
def payments_table(request):
    user = request.user
    role = getattr(user, "role", "")

    # --- PAGINATION ---
    offset = int(request.GET.get("offset", 0))
    limit = int(request.GET.get("limit", 50))
    sort_by = request.GET.get("sort_by", "payment_date")
    sort_dir = request.GET.get("sort_dir", "desc")

    # --- BASE QUERY ---
    company = get_user_company(request)
    qs = Payment.objects.select_related("client", "company").filter(company=company)

    # --- ROLE: Client ---
    if role == "Client":
        linked = getattr(user, "linked_client", None)
        if linked:
            qs = qs.filter(client=linked)

    # --- GLOBAL CLIENT FILTER (home.html input=clientFilter) ---
    client_filter = request.GET.get("client_code", "").strip()
    if client_filter and role in ("Admin", "Operator"):
        qs = qs.filter(client__client_code__icontains=client_filter)

    # --- GENERIC FILTERS ---
    #   filter[field]=value  →  field__icontains=value
    for key, value in request.GET.items():
        qs = qs.annotate(
            operation_type_sort=Case(
                When(operation_kind=1, then="payment_type__name"),
                When(operation_kind=2, then="accrual_type__name"),
                default=Value(""),
                output_field=CharField()
            )
        )
        if key.startswith("filter[") and key.endswith("]") and value:
            field = key[7:-1]  # всё внутри []
            qs = qs.filter(**{f"{field}__icontains": value})

    # --- SORTING ---
    sortable = {
        "operation_type": "operation_type_sort",
        "operation_kind": "operation_kind",
        "operation_kind_label": "operation_kind",
        "client_code": "client__client_code",
        "amount_total": "amount_total",
        "currency": "currency",
        "amount_usd": "amount_usd",
        "payment_date": "payment_date",
    }

    field = sortable.get(sort_by, "payment_date")

    if sort_dir == "desc":
        field = "-" + field

    qs = qs.order_by(field)

    # --- TOTAL / EMPTY ---
    total = qs.count()
    if offset >= total:
        return JsonResponse({"results": [], "has_more": False})

    qs = qs[offset:offset + limit]
    has_more = (offset + qs.count()) < total

    # --- FORMAT OUTPUT ---
    results = []
    for pay in qs:
        row = {
            "id": pay.id,
            "payment_date": pay.payment_date.strftime("%d.%m.%Y"),

            # Вид оплаты/начисления
            "operation_type": (
                pay.payment_type.name if pay.operation_kind == 1 and pay.payment_type
                else pay.accrual_type.name if pay.operation_kind == 2 and pay.accrual_type
                else ""
            ),

            # Тип операции (Оплата/Начисление)
            "operation_kind": pay.operation_kind,
            "operation_kind_label": "Оплата" if pay.operation_kind == 1 else "Начисление",

            # Клиент
            "client_code": pay.client.client_code,

            # Суммы
            "amount_total": float(pay.amount_total),
            "currency": pay.currency,
            "amount_usd": float(pay.amount_usd),

            # Новые поля
            "comment": pay.comment or "",
            "products": pay.products or [],
            "cargos": pay.cargos or [],
        }

        results.append(row)

    return JsonResponse({
        "results": results,
        "has_more": has_more
    })
