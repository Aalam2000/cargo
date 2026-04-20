# cargodb/views.py
import json
import os
import sys

from autoi18n import Translator
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.db.models import Q
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt

from cargo_acc.models import Cargo
from cargo_acc.models import Client
from cargo_acc.models import Product, Payment
from .forms import UserLoginForm


_TRANSLATOR = None


def get_supported_ui_languages():
    langs = [settings.LANGUAGE_CODE]
    langs.extend(
        str(code).strip().lower()
        for code in (settings.AUTO_I18N_TARGET_LANGS or [])
        if str(code).strip()
    )
    return list(dict.fromkeys(langs))


def _get_ui_lang(request):
    lang = (request.COOKIES.get("ui_lang") or "").strip().lower()
    supported = set(get_supported_ui_languages())
    return lang if lang in supported else settings.LANGUAGE_CODE


def _get_translator():
    global _TRANSLATOR
    if _TRANSLATOR is None:
        _TRANSLATOR = Translator(
            cache_dir=os.path.join(settings.BASE_DIR, "translations"),
            source_lang=settings.LANGUAGE_CODE,
        )
    return _TRANSLATOR


def get_base_template_context(request):
    return {
        "app_languages": get_supported_ui_languages(),
        "current_ui_lang": _get_ui_lang(request),
    }


def render_translated(request, template_name, context=None, page_name="page", status=200):
    context = context or {}
    merged_context = {
        **get_base_template_context(request),
        **context,
    }

    html = render_to_string(template_name, merged_context, request=request)

    target_lang = _get_ui_lang(request)
    if target_lang == "ru":
        return HttpResponse(html, status=status)

    try:
        translated_html = _get_translator().translate_html(
            html=html,
            target_lang=target_lang,
            page_name=page_name,
        )
        return HttpResponse(translated_html, status=status)
    except Exception:
        return HttpResponse(html, status=status)


@csrf_exempt
def js_log(request):
    data = json.loads(request.body.decode("utf-8"))
    msg = f"[{data.get('source')}] {data.get('message')}"
    print(msg, file=sys.stdout, flush=True)
    return JsonResponse({"ok": True})


@login_required
def dashboard_view(request):
    return render(request, 'cargo_acc/dashboard.html')


@login_required
def debugging_code_view(request):
    return render(request, 'cargo_acc/debugging_code.html')


@login_required
def orders_view(request):
    return render(request, 'cargo_acc/orders.html')


def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('profile')
    else:
        form = UserLoginForm()
    return render(request, 'registration/login.html', {'form': form})


@login_required
def cargo_table_view(request):
    return render(request, "cargo_acc/cargo_table.html")


@login_required
def cargo_table_config(request):
    role = request.role or ""

    admin_columns = [
        {"field": "cargo_code", "label": "Код", "visible": True},
        {"field": "cargo_description", "label": "Описание", "visible": True},
        {"field": "departure_place", "label": "Место отправки", "visible": True},
        {"field": "destination_place", "label": "Место назначения", "visible": True},
        {"field": "weight", "label": "Вес", "visible": True},
        {"field": "volume", "label": "Объём", "visible": True},
        {"field": "cost", "label": "Стоимость", "visible": True},
        {"field": "insurance", "label": "Страховка", "visible": False},
        {"field": "dimensions", "label": "Габариты", "visible": False},
        {"field": "shipping_date", "label": "Дата отправки", "visible": True},
        {"field": "delivery_date", "label": "Дата доставки", "visible": True},
        {"field": "delivery_time", "label": "Время в пути", "visible": False},
        {"field": "packaging_cost", "label": "Стоимость упаковки", "visible": False},
        {"field": "places_count", "label": "Мест", "visible": False},
        {"field": "tariff_min", "label": "Мин. тариф", "visible": False},
        {"field": "tariff_weight", "label": "Тариф по весу", "visible": False},
        {"field": "qr_code", "label": "QR-код", "visible": False},
        {"field": "qr_created_at", "label": "QR дата", "visible": False},
        {"field": "client", "label": "Клиент", "visible": True},
        {"field": "cargo_status", "label": "Статус", "visible": True},
        {"field": "packaging_type", "label": "Упаковка", "visible": True},
    ]

    client_columns = [
        {"field": "cargo_code", "label": "Код", "visible": True},
        {"field": "cargo_description", "label": "Описание", "visible": True},
        {"field": "weight", "label": "Вес", "visible": True},
        {"field": "volume", "label": "Объём", "visible": True},
        {"field": "cost", "label": "Стоимость", "visible": True},
        {"field": "cargo_status", "label": "Статус", "visible": True},
        {"field": "packaging_type", "label": "Упаковка", "visible": True},
        {"field": "shipping_date", "label": "Дата отправки", "visible": True},
        {"field": "delivery_date", "label": "Дата доставки", "visible": True},
    ]

    default_columns = admin_columns if role in ["Admin", "Operator"] else client_columns
    config = {"columns": default_columns, "page_size": 50}

    table_settings = request.table_settings or {}
    if "cargo_table" in table_settings:
        saved_cfg = table_settings["cargo_table"]
        if isinstance(saved_cfg, dict):
            saved_columns = {c["field"]: c for c in saved_cfg.get("columns", [])}

            merged_columns = []
            for col in default_columns:
                merged_col = col.copy()
                field = merged_col["field"]
                if field in saved_columns:
                    merged_col["visible"] = saved_columns[field].get("visible", merged_col["visible"])
                merged_columns.append(merged_col)

            existing_fields = {c["field"] for c in merged_columns}
            for field, col in saved_columns.items():
                if field not in existing_fields:
                    merged_columns.append(col)

            config["columns"] = merged_columns

            if "page_size" in saved_cfg:
                config["page_size"] = saved_cfg["page_size"]

    return JsonResponse(config)


@login_required
def cargo_table_data(request):
    role = request.role or ""
    company = request.company
    assigned_object = request.assigned_object

    offset = int(request.GET.get("offset", 0))
    limit = int(request.GET.get("limit", 50))

    filters = {k: v for k, v in request.GET.items() if v}

    qs = Cargo.objects.select_related(
        "client", "cargo_status", "packaging_type"
    ).filter(company=company)

    if role == "Client":
        client_obj = assigned_object if isinstance(assigned_object, Client) else None
        if client_obj and client_obj.company_id == company.id:
            qs = qs.filter(client=client_obj)
        else:
            qs = qs.none()

    excluded_fields = [
        "weight", "volume", "cost", "insurance",
        "packaging_cost", "tariff_min", "tariff_weight",
        "places_count",
    ]

    field_map = {
        "cargo": "cargo_code__icontains",
        "cargo_code": "cargo_code__icontains",
        "cargo_description": "cargo_description__icontains",
        "client": "client__client_code__icontains",
        "status": "cargo_status__name__icontains",
        "cargo_status": "cargo_status__name__icontains",
        "packaging_type": "packaging_type__name__icontains",
        "departure_place": "departure_place__icontains",
        "destination_place": "destination_place__icontains",
        "shipping_date": "shipping_date__icontains",
        "delivery_date": "delivery_date__icontains",
    }

    for key, value in filters.items():
        if key in excluded_fields:
            continue
        lookup = field_map.get(key)
        if lookup:
            qs = qs.filter(**{lookup: value})
        elif hasattr(Cargo, key):
            qs = qs.filter(**{f"{key}__icontains": value})

    total = qs.count()

    if offset >= total:
        return JsonResponse({"results": [], "has_more": False})

    sort_by = request.GET.get("sort_by")
    sort_dir = request.GET.get("sort_dir", "asc")

    sortable_fields = {
        "cargo_code": "cargo_code",
        "client": "client__client_code",
        "shipping_date": "shipping_date",
        "delivery_date": "delivery_date",
    }

    if sort_by in sortable_fields:
        order_field = sortable_fields[sort_by]
        if sort_dir == "desc":
            order_field = f"-{order_field}"
        qs = qs.order_by(order_field)

    qs = qs[offset:offset + limit]
    next_offset = offset + qs.count()
    has_more = next_offset < total

    def fmt(d):
        try:
            return d.strftime("%d.%m.%Y") if d else ""
        except Exception:
            return ""

    results = []
    for c in qs:
        results.append({
            "id": c.id,
            "cargo_code": c.cargo_code,
            "cargo_description": c.cargo_description,
            "client": getattr(c.client, "client_code", ""),
            "cargo_status": getattr(c.cargo_status, "name", ""),
            "packaging_type": getattr(c.packaging_type, "name", ""),
            "departure_place": getattr(c, "departure_place", ""),
            "destination_place": getattr(c, "destination_place", ""),
            "weight": f"{c.weight:.2f}" if c.weight else "",
            "volume": f"{c.volume:.2f}" if c.volume else "",
            "cost": f"{c.cost:.2f}" if c.cost else "",
            "insurance": f"{c.insurance:.2f}" if c.insurance else "",
            "dimensions": getattr(c, "dimensions", ""),
            "shipping_date": fmt(getattr(c, "shipping_date", None)),
            "delivery_date": fmt(getattr(c, "delivery_date", None)),
            "delivery_time": getattr(c, "delivery_time", ""),
            "packaging_cost": f"{c.packaging_cost:.2f}" if c.packaging_cost else "",
            "places_count": c.places_count or "",
            "tariff_min": f"{c.tariff_min:.2f}" if c.tariff_min else "",
            "tariff_weight": f"{c.tariff_weight:.2f}" if c.tariff_weight else "",
            "qr_code": getattr(c, "qr_code", ""),
            "qr_created_at": fmt(getattr(c, "qr_created_at", None)),
            "created_at": fmt(getattr(c, "created_at", None)),
            "updated_at": fmt(getattr(c, "updated_at", None)),
        })

    return JsonResponse({"results": results, "has_more": has_more})

@login_required
def all_tables_view(request):
    return render(request, "all_tables.html")


@login_required
def api_all_tables(request):
    company = request.company

    with connection.cursor() as cursor:
        all_tables = connection.introspection.table_names(cursor)

        filtered = []
        for table_name in all_tables:
            if not table_name.startswith("cargo_acc_"):
                continue

            columns_info = connection.introspection.get_table_description(cursor, table_name)
            column_names = [col.name for col in columns_info]

            if table_name == "cargo_acc_company" or "company_id" in column_names:
                filtered.append(table_name.replace("cargo_acc_", ""))

    return JsonResponse(filtered, safe=False)

@login_required
def api_table_data(request):
    """Возвращает первые строки конкретной таблицы"""
    table = request.GET.get("table")
    company = request.company

    if not table:
        return JsonResponse({"error": "No table name"}, status=400)

    if not company:
        return JsonResponse({"error": "No company"}, status=403)

    db_table = f"cargo_acc_{table.replace('cargo_acc_', '')}"

    with connection.cursor() as cursor:
        all_tables = connection.introspection.table_names(cursor)
        allowed_tables = [t for t in all_tables if t.startswith("cargo_acc_")]

        if db_table not in allowed_tables:
            return JsonResponse({"error": "Invalid table"}, status=400)

        columns_info = connection.introspection.get_table_description(cursor, db_table)
        column_names = [col.name for col in columns_info]

        if db_table == "cargo_acc_company":
            cursor.execute(
                f"SELECT * FROM {db_table} WHERE id = %s LIMIT 200",
                [company.id],
            )
        elif "company_id" in column_names:
            cursor.execute(
                f"SELECT * FROM {db_table} WHERE company_id = %s LIMIT 200",
                [company.id],
            )
        else:
            return JsonResponse(
                {"error": "Table is not tenant-scoped"},
                status=403,
            )

        columns = [col[0] for col in cursor.description]
        rows = [dict(zip(columns, r)) for r in cursor.fetchall()]

    return JsonResponse({"columns": columns, "rows": rows})

# ==============================
#  Публичная главная страница (до входа)
# ==============================
def index_view(request):
    """
    Если пользователь авторизован — сразу ведём в /home/
    Если нет — показываем index.html (лендинг/вход)
    """
    if request.user.is_authenticated:
        return redirect("home")
    return render_translated(request, "index.html", page_name="index")


# ==============================
#  Домашняя страница после входа
# ==============================
@login_required
def home_view(request):
    """
    После входа — страница с данными, фильтрацией и таблицами.
    """
    user = request.user
    role = getattr(user, "role", "")
    company = request.company
    client_id = request.GET.get("client_id")
    product_code = request.GET.get("product_code", "").strip()
    cargo_code = request.GET.get("cargo_code", "").strip()

    products = Product.objects.select_related(
        "cargo_status", "client", "warehouse", "company"
    ).filter(company=company)
    payments = Payment.objects.select_related(
        "client", "company"
    ).filter(company=company)

    if role == "Client":
        client_obj = getattr(user, "linked_client", None)
        if client_obj and getattr(client_obj, "company_id", None) == getattr(company, "id", None):
            products = products.filter(client_id=client_obj.id)
            payments = payments.filter(client_id=client_obj.id)
        else:
            products = products.none()
            payments = payments.none()

    elif role == "Operator" and client_id:
        products = products.filter(client_id=client_id, client__company=company)
        payments = payments.filter(client_id=client_id, client__company=company)

    if product_code:
        products = products.filter(product_code__icontains=product_code)

    if cargo_code:
        products = products.filter(cargo__cargo_code__icontains=cargo_code, cargo__company=company)

    delivered = products.filter(
        Q(cargo_status__name__icontains="достав") |
        Q(cargo_status__name__icontains="выдан")
    )
    in_transit = products.exclude(id__in=delivered.values_list("id", flat=True))
    clients = Client.objects.filter(company=company).order_by("client_code") if role == "Operator" else []

    context = {
        "role": role,
        "delivered": delivered,
        "in_transit": in_transit,
        "payments": payments.order_by("-payment_date"),
        "clients": clients,
        "selected_client": client_id,
    }

    return render_translated(request, "home.html", context=context, page_name="home")


# ==============================
#  Расчет баланса клиента + последний платеж
# ==============================
@login_required
def client_balance(request):
    role = request.role or ""
    company = request.company
    assigned_object = request.assigned_object
    client_code = request.GET.get("client_code", "").strip()

    total_paid = 0.0
    last_payment_date = None
    last_payment_amount = 0.0

    if role == "Client":
        client_obj = assigned_object if isinstance(assigned_object, Client) else None
        if client_obj and client_obj.company_id == company.id:
            payments = Payment.objects.filter(
                company=company,
                client=client_obj,
            ).order_by("-payment_date")
            total_paid = payments.aggregate(total=Sum("amount_total")).get("total") or 0
            if payments.exists():
                last = payments.first()
                last_payment_date = last.payment_date
                last_payment_amount = last.amount_total

    elif role in ["Admin", "Operator"] and client_code:
        if client_code == "self":
            return JsonResponse({"total_paid": 0})

        client = Client.objects.filter(
            company=company,
            client_code=client_code,
        ).first()

        if client:
            payments = Payment.objects.filter(
                company=company,
                client=client,
            ).order_by("-payment_date")
            total_paid = payments.aggregate(total=Sum("amount_total")).get("total") or 0
            if payments.exists():
                last = payments.first()
                last_payment_date = last.payment_date
                last_payment_amount = last.amount_total

    result = {
        "total_paid": float(total_paid),
        "last_payment_date": last_payment_date.strftime("%d.%m.%Y") if last_payment_date else "",
        "last_payment_amount": float(last_payment_amount) if last_payment_amount else 0.0,
    }

    return JsonResponse(result)

@login_required
def api_user_role(request):
    """Возвращает текущую роль авторизованного пользователя."""
    user = request.user
    role = getattr(user, "role", None)
    return JsonResponse({"role": role or "Unknown"})
