# cargodb/views.py
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render

from cargo_acc.models import Product
from .forms import UserLoginForm


# @login_required
# def profile_view(request):
#     return render(request, 'accounts/profile.html')

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
    return render(request, 'index.html')


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
    config = (user.table_settings or {}).get("cargo_table")
    if not config:
        config = {
            "columns": [
                {"field": "product_code", "label": "Код груза", "visible": True},
                {"field": "client_id", "label": "Клиент", "visible": True},
                {"field": "cargo_status_id", "label": "Статус", "visible": True},
            ],
            "page_size": 50,
        }
    return JsonResponse(config)


@login_required
def cargo_table_data(request):
    offset = int(request.GET.get("offset", 0))
    limit = int(request.GET.get("limit", 50))
    filters = {
        "client": request.GET.get("client"),
        "company": request.GET.get("company"),
        "warehouse": request.GET.get("warehouse"),
        "status": request.GET.get("status"),
    }

    qs = (
        Product.objects
        .select_related("client", "company", "warehouse", "cargo_status")
        .only("product_code", "client__client_code", "company__name", "warehouse__name", "cargo_status__name")
    )

    # ====== Фильтры ======
    if filters["client"]:
        qs = qs.filter(client__client_code__icontains=filters["client"])
    if filters["company"]:
        qs = qs.filter(company__name__icontains=filters["company"])
    if filters["warehouse"]:
        qs = qs.filter(warehouse__name__icontains=filters["warehouse"])
    if filters["status"]:
        qs = qs.filter(cargo_status__name__icontains=filters["status"])

    total = qs.count()
    qs = qs[offset: offset + limit]

    results = []
    for p in qs:
        results.append({
            "product_code": p.product_code,
            "client_id": getattr(p.client, "client_code", ""),
            "cargo_status_id": getattr(p.cargo_status, "name", ""),
            "company": getattr(p.company, "name", ""),
            "warehouse": getattr(p.warehouse, "name", "")
        })

    has_more = offset + limit < total
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
