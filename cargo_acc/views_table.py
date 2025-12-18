# cargo_acc/views_table.py

import json
import logging
import os

import transliterate
from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q
from django.forms.models import model_to_dict
from django.http import JsonResponse
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from cargo_acc.company_utils import get_user_company, get_log_meta
from cargo_acc.models import SystemActionLog
from .models import Company, Warehouse, CargoType, CargoStatus, PackagingType, Image, Product, Client, AccrualType, \
    PaymentType, CurrencyRate, Tariff
from .serializers import CompanySerializer, ClientSerializer, WarehouseSerializer, CargoTypeSerializer, \
    CargoStatusSerializer, PackagingTypeSerializer, ImageSerializer, AccrualTypeSerializer, PaymentTypeSerializer, \
    CurrencyRateSerializer, TariffSerializer

logger = logging.getLogger(__name__)

# === Маппинг моделей и разрешённых полей ===
TABLES = {
    "warehouses": {
        "model": "cargo_acc.Warehouse",
        "fields": ["name", "address"],
        "search_field": "name",
    },
    "cargo-types": {
        "model": "cargo_acc.CargoType",
        "fields": ["name", "description"],
        "search_field": "name",
    },
    "cargo-statuses": {
        "model": "cargo_acc.CargoStatus",
        "fields": ["name", "description"],
        "search_field": "name",
    },
    "packaging-types": {
        "model": "cargo_acc.PackagingType",
        "fields": ["name", "description"],
        "search_field": "name",
    },
    "accrual-types": {
        "model": "cargo_acc.AccrualType",
        "fields": ["name", "description", "default_amount"],
        "search_field": "name",
    },
    "payment-types": {
        "model": "cargo_acc.PaymentType",
        "fields": ["name", "description"],
        "search_field": "name",
    },
    "tariffs": {
        "model": "cargo_acc.Tariff",
        "fields": [
            "id",
            "name",
            "cargo_type",
            "calc_mode",
            "base_rate",
            "packaging_rate",
            "insurance_percent",
            "minimal_cost",
        ],
        "search_field": "name",
    },

    "currency-rates": {
        "model": "cargo_acc.CurrencyRate",
        "fields": [
            "id",
            "date",
            "currency",
            "rate",
            "custom_rate",
            "conversion_percent",
        ],
        "search_field": "currency",
    },

}


@login_required
def get_table(request, model_name):
    """
    Универсальная вьюха:
    - search
    - sort
    - pagination
    - универсальный вывод
    """

    if model_name not in TABLES:
        return JsonResponse({"error": "unknown model"}, status=400)

    cfg = TABLES[model_name]

    # === модель ===
    try:
        Model = apps.get_model(cfg["model"])
    except Exception as e:

        return JsonResponse({"error": "model_error"}, status=500)

    # === параметры ===
    search_query = request.GET.get("search", "").strip()
    sort_field = request.GET.get("sort", "id")
    sort_dir = request.GET.get("dir", "asc")
    page_size = int(request.GET.get("page_size", 10))
    page = request.GET.get("page", 1)

    # === проверяем поле сортировки ===
    allowed_sort = ["id"] + cfg["fields"]
    if sort_field not in allowed_sort:
        sort_field = "id"

    order = sort_field if sort_dir == "asc" else f"-{sort_field}"

    # === база queryset ===
    company = get_user_company(request)
    qs = Model.objects.all() if not hasattr(Model, "company") else Model.objects.filter(company=company)
    # === search ===
    search_field = cfg["search_field"]
    if search_query:
        qs = qs.filter(**{f"{search_field}__icontains": search_query})

    # === сортировка ===
    qs = qs.order_by(order)

    # === пагинация ===
    paginator = Paginator(qs, page_size)
    try:
        page_obj = paginator.page(page)
    except EmptyPage:
        return JsonResponse({
            "results": [],
            "page": page,
            "total_pages": paginator.num_pages
        })

    # === формируем JSON ===
    results = []
    for obj in page_obj:
        row = {}
        for f in cfg["fields"]:
            val = getattr(obj, f, "")
            # company → company.name
            if f == "company":
                try:
                    val = obj.company.name if obj.company else ""
                except:
                    val = ""
            row[f] = val
        row["id"] = obj.id
        results.append(row)

    return JsonResponse({
        "results": results,
        "page": page,
        "total_pages": paginator.num_pages,
        "fields": cfg["fields"]
    })


def transliterate_filename(filename):
    """API для записи латиницей."""
    name, ext = os.path.splitext(filename)
    # Транслитерация имени файла с кириллицы на латиницу
    return transliterate.translit(name, 'ru', reversed=True) + ext


# === ViewSet модели ===
# ViewSet для Компаний
class CompanyViewSet(viewsets.ModelViewSet):
    serializer_class = CompanySerializer

    def get_queryset(self):
        company = get_user_company(self.request)
        return Company.objects.filter(id=company.id)


# ViewSet для Клиентов
class ClientViewSet(viewsets.ModelViewSet):
    serializer_class = ClientSerializer

    def get_queryset(self):
        company = get_user_company(self.request)
        sort_by = self.request.query_params.get("sort_by", "client_code")
        return Client.objects.filter(company=company).order_by(sort_by)


# ================================
#     ЕДИНЫЕ ПРАВИЛЬНЫЕ СПРАВОЧНИКИ
# ================================

# --- СКЛАДЫ ---
class WarehouseViewSet(viewsets.ModelViewSet):
    serializer_class = WarehouseSerializer

    def get_queryset(self):
        company = get_user_company(self.request)
        sort_by = self.request.query_params.get("sort_by", "name")
        return Warehouse.objects.filter(company=company).order_by(sort_by)

    # важнейшая строка — иначе DRF требует ВСЕ поля
    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)

    def perform_create(self, serializer):
        company = get_user_company(self.request)
        serializer.save(company=company)

    def perform_update(self, serializer):
        company = get_user_company(self.request)
        serializer.save(company=company)


# --- ТИПЫ ГРУЗОВ ---
class CargoTypeViewSet(viewsets.ModelViewSet):
    serializer_class = CargoTypeSerializer

    def get_queryset(self):
        company = get_user_company(self.request)
        sort_by = self.request.query_params.get("sort_by", "name")
        return CargoType.objects.filter(company=company).order_by(sort_by)

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)

    def perform_create(self, serializer):
        company = get_user_company(self.request)
        serializer.save(company=company)

    def perform_update(self, serializer):
        company = get_user_company(self.request)
        serializer.save(company=company)


# --- СТАТУСЫ ГРУЗОВ ---
class CargoStatusViewSet(viewsets.ModelViewSet):
    serializer_class = CargoStatusSerializer

    def get_queryset(self):
        company = get_user_company(self.request)
        sort_by = self.request.query_params.get("sort_by", "name")
        return CargoStatus.objects.filter(company=company).order_by(sort_by)

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)

    def perform_create(self, serializer):
        company = get_user_company(self.request)
        serializer.save(company=company)

    def perform_update(self, serializer):
        company = get_user_company(self.request)
        serializer.save(company=company)


# --- ТИПЫ УПАКОВКИ ---
class PackagingTypeViewSet(viewsets.ModelViewSet):
    serializer_class = PackagingTypeSerializer

    def get_queryset(self):
        company = get_user_company(self.request)
        sort_by = self.request.query_params.get("sort_by", "name")
        return PackagingType.objects.filter(company=company).order_by(sort_by)

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)

    def perform_create(self, serializer):
        company = get_user_company(self.request)
        serializer.save(company=company)

    def perform_update(self, serializer):
        company = get_user_company(self.request)
        serializer.save(company=company)


# --- ТИПЫ НАЧИСЛЕНИЙ ---
class AccrualTypeViewSet(viewsets.ModelViewSet):
    serializer_class = AccrualTypeSerializer

    def get_queryset(self):
        company = get_user_company(self.request)
        sort_by = self.request.query_params.get("sort_by", "name")
        return AccrualType.objects.filter(company=company).order_by(sort_by)

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)

    def perform_create(self, serializer):
        company = get_user_company(self.request)
        serializer.save(company=company)

    def perform_update(self, serializer):
        company = get_user_company(self.request)
        serializer.save(company=company)


# --- ТИПЫ ПЛАТЕЖЕЙ ---
class PaymentTypeViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentTypeSerializer

    def get_queryset(self):
        company = get_user_company(self.request)
        sort_by = self.request.query_params.get("sort_by", "name")
        return PaymentType.objects.filter(company=company).order_by(sort_by)

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)

    def perform_create(self, serializer):
        company = get_user_company(self.request)
        serializer.save(company=company)

    def perform_update(self, serializer):
        company = get_user_company(self.request)
        serializer.save(company=company)


# --- ТАРИФЫ ---
class TariffViewSet(viewsets.ModelViewSet):
    serializer_class = TariffSerializer

    def get_queryset(self):
        company = get_user_company(self.request)
        return Tariff.objects.filter(company=company).order_by("name")

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)

    def perform_create(self, serializer):
        company = get_user_company(self.request)
        serializer.save(company=company)

    def perform_update(self, serializer):
        company = get_user_company(self.request)
        serializer.save(company=company)


# --- КУРСЫ ВАЛЮТ ---
class CurrencyRateViewSet(viewsets.ModelViewSet):
    serializer_class = CurrencyRateSerializer

    def get_queryset(self):
        return CurrencyRate.objects.all().order_by("-date")

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)


# ViewSet для Изображений
class ImageViewSet(viewsets.ModelViewSet):
    serializer_class = ImageSerializer

    def get_queryset(self):
        company = get_user_company(self.request)
        return Image.objects.filter(company=company)

    def perform_create(self, serializer):
        image = self.request.FILES['image_file']
        image.name = transliterate_filename(image.name)
        company = get_user_company(self.request)
        serializer.save(image_file=image, company=company)


# ViewSet для Товаров
class ProductPagination(PageNumberPagination):
    page_size = 20  # Количество записей на странице
    page_size_query_param = 'page_size'


# ============================================================
#     ProductsTableViewSet  —  CRUD для товара
# ============================================================
class ProductsTableViewSet(ViewSet):
    """
    • list  — список для product_table.html
    • retrieve — отдаёт ВСЕ данные товара (для модалки!)
    • create — создание товара
    • update — изменение товара
    """

    # -------------------------------------------
    # LIST — (как было, без логики логирования)
    # -------------------------------------------
    def list(self, request):
        offset = int(request.GET.get("offset", 0))
        limit = int(request.GET.get("limit", 30))

        sort_by = request.GET.get("sort_by", "product_code")
        sort_dir = request.GET.get("sort_dir", "asc")

        SORTABLE = {
            "product_code": "product_code",
            "client": "client__client_code",
            "cargo": "cargo__cargo_code",
            "warehouse": "warehouse__name",
        }

        order_field = SORTABLE.get(sort_by)
        if order_field and sort_dir == "desc":
            order_field = "-" + order_field

        company = get_user_company(request)
        qs = Product.objects.filter(company=company).select_related(
            "client", "cargo", "warehouse", "cargo_status"
        )

        user = request.user
        role = getattr(user, "role", "")

        if role == "Client":
            linked = getattr(user, "linked_client", None)
            if not linked:
                return Response({"results": [], "total": 0, "has_more": False})
            qs = qs.filter(client_id=linked.id)

        elif role in ("Admin", "Operator"):
            qs = qs.filter(company=company)
        else:
            return Response({"results": [], "total": 0, "has_more": False})

        # фильтры (разрешённые поля)
        FILTERABLE = {
            "product_code": "product_code",
            "client": "client__client_code",
            "cargo": "cargo__cargo_code",
            "warehouse": "warehouse__name",
            "cargo_status": "cargo_status__name",
        }

        for key, value in request.GET.items():
            if not (key.startswith("filter[") and key.endswith("]")):
                continue

            val = (value or "").strip()
            if not val:
                continue

            field = key[7:-1]
            orm_field = FILTERABLE.get(field)
            if not orm_field:
                continue

            qs = qs.filter(**{f"{orm_field}__icontains": val})

        if order_field:
            qs = qs.order_by(order_field)

        total = qs.count()
        items = qs[offset: offset + limit]
        has_more = offset + limit < total

        results = []
        for p in items:
            results.append({
                "id": p.id,
                "product_code": p.product_code or "",
                "client": p.client.client_code if p.client else "",
                "cargo": p.cargo.cargo_code if p.cargo else "",
                "cargo_status": p.cargo_status.name if p.cargo_status else "",
                "warehouse": p.warehouse.name if p.warehouse else "",
                "weight": p.weight,
                "volume": p.volume,
                "cost": p.cost,
                "images": [],  # пока заглушка, иначе JS сломается
            })

        return Response({"results": results, "total": total, "has_more": has_more})

    # ----------------------------------------------------
    # RETRIEVE — отдаёт ПОЛНУЮ строку товара для модалки
    # ----------------------------------------------------
    def retrieve(self, request, pk=None):
        company = get_user_company(request)

        try:
            product = Product.objects.get(id=pk, company=company)
        except Product.DoesNotExist:
            return Response({"error": "not_found"}, status=404)

        # ЛОГИ (универсальная функция)
        meta = get_log_meta("Product", product.id)

        return Response({
            "id": product.id,
            "product_code": product.product_code,
            "client": product.client.client_code if product.client else "",

            # ДАТА И АВТОР ЗАПИСИ — СЮДА ПОЛЕ ДЛЯ МОДАЛКИ
            "record_date": meta["created_at"],
            "created_by": meta["created_by"],

            "cargo_description": product.cargo_description,
            "departure_place": product.departure_place,
            "destination_place": product.destination_place,
            "weight": product.weight,
            "volume": product.volume,
            "cost": product.cost,
            "delivery_time": product.delivery_time,
            "shipping_date": product.shipping_date,
            "delivery_date": product.delivery_date,
            "comment": product.comment,
        })

    # ----------------------------------------------------
    # CREATE — создание товара + логирование
    # ----------------------------------------------------
    def create(self, request):
        data = request.data
        company = get_user_company(request)

        client_id = data.get("client_id")
        if not client_id:
            return Response({"error": "client required"}, status=400)

        try:
            client = Client.objects.get(id=client_id, company=company)
        except Client.DoesNotExist:
            return Response({"error": "client_not_found"}, status=404)

        p = Product.objects.create(
            client=client,
            company=company,
            warehouse_id=data.get("warehouse_id"),
            cargo_type_id=data.get("cargo_type_id"),
            cargo_status_id=data.get("cargo_status_id"),
            packaging_type_id=data.get("packaging_type_id"),
            product_code=data.get("product_code"),
            comment=data.get("comment", "")
        )

        # ЛОГ СОЗДАНИЯ
        SystemActionLog.objects.create(
            company=company,
            model_name="Product",
            object_id=p.id,
            action="create",
            old_data=None,
            new_data=model_to_dict(p),
            diff={"created": True},
            operator=request.user,
            ip=request.META.get("REMOTE_ADDR")
        )

        return Response({"id": p.id, "status": "ok"})

    # ----------------------------------------------------
    # UPDATE — обновление товара + логирование diff
    # ----------------------------------------------------
    def update(self, request, pk=None):

        company = get_user_company(request)

        try:
            product = Product.objects.get(id=pk, company=company)
            old_data = model_to_dict(product)
        except Product.DoesNotExist:
            return Response({"error": "not_found"}, status=404)

        data = request.data

        fields = [
            "cargo_description", "departure_place", "destination_place",
            "weight", "volume", "cost", "delivery_time",
            "shipping_date", "delivery_date", "comment"
        ]

        for f in fields:
            if f in data:
                setattr(product, f, data[f])

        product.save()

        new_data = model_to_dict(product)

        diff = {}
        for k in new_data:
            if old_data.get(k) != new_data.get(k):
                diff[k] = [old_data.get(k), new_data.get(k)]

        # ЛОГ ИЗМЕНЕНИЯ
        SystemActionLog.objects.create(
            company=company,
            model_name="Product",
            object_id=product.id,
            action="update",
            old_data=old_data,
            new_data=new_data,
            diff=diff,
            operator=request.user,
            ip=request.META.get("REMOTE_ADDR")
        )

        return Response({"status": "ok"})


# ================================
#  НОВЫЙ API ДЛЯ ТАБЛИЦЫ ТОВАРОВ
#  /api/products_table/
# ================================
@login_required
def products_table_view(request):
    """
    Лёгкий API для home.html — только чтение.
    """

    try:
        limit = int(request.GET.get("limit", 50))
        offset = int(request.GET.get("offset", 0))
    except:
        return JsonResponse({"error": "bad pagination"}, status=400)

    tab = request.GET.get("tab", "").strip()
    sort_by = request.GET.get("sort_by", "product_code")
    sort_dir = request.GET.get("sort_dir", "asc")

    company = get_user_company(request)
    qs = Product.objects.filter(company=company).select_related(
        "client", "warehouse", "cargo_type", "cargo_status"
    )

    user = request.user
    role = getattr(user, "role", "")

    if role == "Client":
        linked = getattr(user, "linked_client", None)
        if not linked:
            return JsonResponse({"results": [], "total": 0, "has_more": False})
        qs = qs.filter(client_id=linked.id)
    elif role not in ("Admin", "Operator"):
        return JsonResponse({"results": [], "total": 0, "has_more": False})

    delivered_filter = (
            Q(cargo_status__name__icontains="отдан") |
            Q(cargo_status__name__icontains="выдан") |
            Q(delivery_date__isnull=False)
    )

    if tab == "delivered":
        qs = qs.filter(delivered_filter)
    elif tab == "in_transit":
        qs = qs.exclude(delivered_filter)
    else:
        return JsonResponse({"error": "bad tab"}, status=400)
    # -------- FILTERING --------
    FILTERABLE = {
        "product_code": "product_code",
        "client": "client__client_code",
        "warehouse": "warehouse__name",
        "cargo_status": "cargo_status__name",
    }

    for key, value in request.GET.items():
        if not (key.startswith("filter[") and key.endswith("]")):
            continue

        val = (value or "").strip()
        if not val:
            continue

        field = key[7:-1]
        orm_field = FILTERABLE.get(field)
        if not orm_field:
            continue

        # client-фильтр допустим только для Admin/Operator
        if field == "client" and role not in ("Admin", "Operator"):
            continue

        qs = qs.filter(**{f"{orm_field}__icontains": val})
    # -------- SORTING ----------
    SORTABLE = {
        "product_code": "product_code",
        "shipping_date": "shipping_date",
        "delivery_date": "delivery_date",
        "warehouse": "warehouse__name",
        "cargo_status": "cargo_status__name",
    }

    if role in ("Admin", "Operator"):
        SORTABLE["client"] = "client__client_code"

    # record_date — сортируем через ID (первичную дату создания)
    if sort_by == "record_date":
        qs = qs.order_by("-id" if sort_dir == "desc" else "id")
    else:
        field = SORTABLE.get(sort_by, "product_code")
        if sort_dir == "desc":
            field = "-" + field
        qs = qs.order_by(field)

    # -------- PAGINATION --------
    total = qs.count()
    items = qs[offset: offset + limit]
    has_more = offset + limit < total

    # -------- RESULT DATA --------
    results = []

    for p in items:
        meta = get_log_meta("Product", p.id)
        record_date = (
            meta["created_at"].strftime("%Y-%m-%d")
            if meta["created_at"] else ""
        )

        results.append({
            "id": p.id,
            "product_code": p.product_code,
            "record_date": record_date,
            "shipping_date": p.shipping_date.strftime("%Y-%m-%d") if p.shipping_date else "",
            "delivery_date": p.delivery_date.strftime("%Y-%m-%d") if p.delivery_date else "",
            "client": p.client.client_code if p.client else "",
            "warehouse": p.warehouse.name if p.warehouse else "",
            "cargo_status": p.cargo_status.name if p.cargo_status else "",
        })

    return JsonResponse({
        "results": results,
        "total": total,
        "has_more": has_more
    })


# Заполнение Комапании
@login_required
def get_company(request, pk):
    from .models import Company

    # Компания пользователя
    user_company_id = get_user_company(request).id

    # Если запрос к чужой компании — запрет
    if pk != user_company_id:
        return JsonResponse({"error": "forbidden"}, status=403)

    try:
        obj = Company.objects.get(id=user_company_id)
    except Company.DoesNotExist:
        return JsonResponse({"error": "not found"}, status=404)

    return JsonResponse({
        "id": obj.id,
        "name": obj.name,
        "registration": obj.registration,
        "tax_id": obj.tax_id,
        "ogrn": obj.ogrn,
        "legal_address": obj.legal_address,
        "actual_address": obj.actual_address,
        "representative_fullname": obj.representative_fullname,
        "representative_basis": obj.representative_basis,
        "phone": obj.phone,
        "email": obj.email,
        "description": obj.description,

        "prefix": obj.prefix,

        "director_fullname": obj.director_fullname,
    })


@login_required
def update_company(request, pk):
    from .models import Company

    if request.method != "PUT":
        return JsonResponse({"error": "method not allowed"}, status=405)

    user_company_id = get_user_company(request).id

    # Запрещаем редактировать чужую компанию
    if pk != user_company_id:
        return JsonResponse({"error": "forbidden"}, status=403)

    try:
        obj = Company.objects.get(id=user_company_id)
    except Company.DoesNotExist:
        return JsonResponse({"error": "not found"}, status=404)

    data = json.loads(request.body)
    logger.error(f"CREATE PARSED DATA: {data}")

    # Перебираем только существующие поля модели
    allowed_fields = {
        "name", "registration", "tax_id", "ogrn",
        "legal_address", "actual_address",
        "representative_fullname", "representative_basis",
        "phone", "email", "description",
        "prefix",
        "director_fullname"
    }

    for field, value in data.items():
        if field in allowed_fields:
            setattr(obj, field, value)

    obj.save()

    return JsonResponse({"success": True})


@login_required
def api_generate_client_code(request):
    from cargo_acc.services.code_generator import generate_client_code
    company = get_user_company(request)
    code = generate_client_code(company)
    return JsonResponse({"client_code": code})


@login_required
def api_generate_product_code(request):
    from cargo_acc.services.code_generator import generate_product_code
    import json

    data = json.loads(request.body)
    client_id = data.get("client_id")

    if not client_id:
        return JsonResponse({"error": "client_id required"}, status=400)

    try:
        company = get_user_company(request)
        client = Client.objects.get(id=client_id, company=company)
    except Client.DoesNotExist:
        return JsonResponse({"error": "client not found"}, status=404)

    code = generate_product_code(client)
    return JsonResponse({"product_code": code})


@login_required
def api_generate_cargo_code(request):
    from cargo_acc.services.code_generator import generate_cargo_code
    import json

    data = json.loads(request.body)
    client_id = data.get("client_id")

    if not client_id:
        return JsonResponse({"error": "client_id required"}, status=400)

    try:
        company = get_user_company(request)
        client = Client.objects.get(id=client_id, company=company)
    except Client.DoesNotExist:
        return JsonResponse({"error": "client not found"}, status=404)

    code = generate_cargo_code(client)
    return JsonResponse({"cargo_code": code})
