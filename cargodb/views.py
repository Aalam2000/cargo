# cargodb/views.py
import json
import sys

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from cargo_acc.models import Cargo
from .forms import UserLoginForm

from cargo_acc.models import Product, Payment, Client

# @login_required
# def profile_view(request):
#     return render(request, 'accounts/profile.html')

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


def index_view(request):
    if request.user.is_authenticated:
        return redirect("cargo_table")  # после логина — сразу таблица грузов
    return render(request, "index.html")  # до логина — обычная главная


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
    user = request.user
    role = getattr(user, "role", "")

    # дефолтные колонки
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

    # выбираем базовый шаблон
    default_columns = admin_columns if role in ["Admin", "Operator"] else client_columns
    config = {"columns": default_columns, "page_size": 50}

    # если у пользователя уже сохранены настройки — применяем
    user_settings = getattr(user, "table_settings", None) or {}
    if "cargo_table" in user_settings:
        saved_cfg = user_settings["cargo_table"]
        if isinstance(saved_cfg, dict):
            saved_columns = {c["field"]: c for c in saved_cfg.get("columns", [])}

            # объединяем дефолтные с сохранёнными (только visible и порядок)
            merged_columns = []
            for col in default_columns:
                field = col["field"]
                if field in saved_columns:
                    col["visible"] = saved_columns[field].get("visible", col["visible"])
                merged_columns.append(col)

            # добавляем пользовательские поля, которых больше нет в дефолтах
            for field, col in saved_columns.items():
                if field not in [c["field"] for c in merged_columns]:
                    merged_columns.append(col)

            config["columns"] = merged_columns

            # обновляем page_size, если есть
            if "page_size" in saved_cfg:
                config["page_size"] = saved_cfg["page_size"]

    return JsonResponse(config)


@login_required
def cargo_table_data(request):
    user = request.user
    offset = int(request.GET.get("offset", 0))
    limit = int(request.GET.get("limit", 50))
    role = getattr(user, "role", "")

    # все возможные фильтры, приходящие с фронта
    filters = {k: v for k, v in request.GET.items() if v}

    qs = Cargo.objects.select_related("client", "cargo_status", "packaging_type")

    # --- РОЛЬ КЛИЕНТА ---
    if role == "Client" and user.client_code:
        qs = qs.filter(client__client_code=user.client_code)

    # --- Универсальная фильтрация (без числовых и суммовых полей) ---
    # исключаем поля с цифрами и суммами
    excluded_fields = [
        "weight", "volume", "cost", "insurance",
        "packaging_cost", "tariff_min", "tariff_weight",
        "places_count",
    ]

    # маппинг фильтров на реальные поля модели
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

    # применяем фильтры динамически
    for key, value in filters.items():
        if key in excluded_fields:
            continue
        lookup = field_map.get(key)
        if lookup:
            qs = qs.filter(**{lookup: value})
        elif hasattr(Cargo, key):
            qs = qs.filter(**{f"{key}__icontains": value})

    # --- Пагинация ---
    total = qs.count()

    # если offset превышает общее число строк — вернуть пусто
    if offset >= total:
        return JsonResponse({"results": [], "has_more": False})

    # --- Сортировка ---
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


    # --- Формат вывода ---
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
    with connection.cursor() as cursor:
        all_tables = connection.introspection.table_names(cursor)
    # Берём все таблицы из cargo_acc, включая вспомогательные
    filtered = [t.replace("cargo_acc_", "") for t in all_tables if t.startswith("cargo_acc_")]
    return JsonResponse(filtered, safe=False)


@login_required
def api_table_data(request):
    """Возвращает первые строки конкретной таблицы"""
    table = request.GET.get("table")
    if not table:
        return JsonResponse({"error": "No table name"}, status=400)

    with connection.cursor() as cursor:
        cursor.execute(f"SELECT * FROM {table} LIMIT 200")
        columns = [col[0] for col in cursor.description]
        rows = [dict(zip(columns, r)) for r in cursor.fetchall()]
    return JsonResponse({"columns": columns, "rows": rows})


def home_view(request):
    return render(request, 'index.html')


@login_required
def home_view(request):
    user = request.user
    role = user.role
    client_id = request.GET.get("client_id")
    product_code = request.GET.get("product_code", "").strip()
    cargo_code = request.GET.get("cargo_code", "").strip()

    products = Product.objects.select_related("cargo_status", "client", "warehouse", "company")
    payments = Payment.objects.select_related("client", "company")

    if role == "Client":
        client_obj = getattr(user, "linked_client", None)
        if client_obj:
            products = products.filter(client_id=client_obj.id)
            payments = payments.filter(client_id=client_obj.id)
    elif role == "Operator" and client_id:
        products = products.filter(client_id=client_id)
        payments = payments.filter(client_id=client_id)

    if product_code:
        products = products.filter(product_code__icontains=product_code)

        # Все товары, у которых статус содержит "Выдан" или "Достав"
    delivered = products.filter(cargo_status__name__icontains="достав") | products.filter(
        cargo_status__name__icontains="выдан"
    )

    # Остальные считаем "в пути"
    in_transit = products.exclude(id__in=delivered.values_list("id", flat=True))
    clients = Client.objects.all().order_by("client_code") if role == "Operator" else []

    return render(request, "home.html", {
        "role": role,
        "delivered": delivered,
        "in_transit": in_transit,
        "payments": payments.order_by("-payment_date"),
        "clients": clients,
        "selected_client": client_id,
    })
