# cargo_acc/views_table.py

import os
import logging
import transliterate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage
from django.apps import apps
from rest_framework.pagination import PageNumberPagination

from rest_framework import viewsets
from .serializers import CompanySerializer, ClientSerializer, WarehouseSerializer, CargoTypeSerializer, \
    CargoStatusSerializer, PackagingTypeSerializer, ImageSerializer, ProductSerializer, CargoSerializer, \
    CarrierCompanySerializer, VehicleSerializer, TransportBillSerializer, CargoMovementSerializer, AccrualTypeSerializer
from .models import Company, Warehouse, CargoType, CargoStatus, PackagingType, Image, Product, Cargo, \
    CarrierCompany, Vehicle, TransportBill, CargoMovement, Client, AccrualType

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
        logger.error(f"Model load error: {e}")
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
    qs = Model.objects.all()

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
    queryset = Company.objects.all()
    serializer_class = CompanySerializer

    def get_queryset(self):
        queryset = super().get_queryset()  # Получаем первоначальный queryset из родительского метода
        sort_by = self.request.query_params.get('sort_by', 'name')  # Получаем параметр для сортировки из запроса
        return queryset.order_by(sort_by)  # Сортируем по переданному полю (по умолчанию 'name')


# ViewSet для Клиентов
class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer

    def get_queryset(self):
        queryset = super().get_queryset()  # Получаем первоначальный queryset из родительского метода
        sort_by = self.request.query_params.get('sort_by', 'client_code')  # Получаем параметр для сортировки из запроса
        return queryset.order_by(sort_by)  # Сортируем по переданному полю (по умолчанию 'name')


# ViewSet для Складов
class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer

    def get_queryset(self):
        queryset = super().get_queryset()  # Получаем первоначальный queryset из родительского метода
        sort_by = self.request.query_params.get('sort_by', 'name')  # Получаем параметр для сортировки из запроса
        return queryset.order_by(sort_by)  # Сортируем по переданному полю (по умолчанию 'name')


# ViewSet для Типов Груза
class CargoTypeViewSet(viewsets.ModelViewSet):
    queryset = CargoType.objects.all()
    serializer_class = CargoTypeSerializer

    def get_queryset(self):
        queryset = super().get_queryset()  # Получаем первоначальный queryset из родительского метода
        sort_by = self.request.query_params.get('sort_by', 'name')  # Получаем параметр для сортировки из запроса
        return queryset.order_by(sort_by)  # Сортируем по переданному полю (по умолчанию 'name')


# ViewSet для Статусов Груза
class CargoStatusViewSet(viewsets.ModelViewSet):
    queryset = CargoStatus.objects.all()
    serializer_class = CargoStatusSerializer

    def get_queryset(self):
        queryset = super().get_queryset()  # Получаем первоначальный queryset из родительского метода
        sort_by = self.request.query_params.get('sort_by', 'name')  # Получаем параметр для сортировки из запроса
        return queryset.order_by(sort_by)  # Сортируем по переданному полю (по умолчанию 'name')


# ViewSet для Типов Упаковок
class PackagingTypeViewSet(viewsets.ModelViewSet):
    queryset = PackagingType.objects.all()
    serializer_class = PackagingTypeSerializer

    def get_queryset(self):
        queryset = super().get_queryset()  # Получаем первоначальный queryset из родительского метода
        sort_by = self.request.query_params.get('sort_by', 'name')  # Получаем параметр для сортировки из запроса
        return queryset.order_by(sort_by)  # Сортируем по переданному полю (по умолчанию 'name')

class AccrualTypeViewSet(viewsets.ModelViewSet):
    queryset = AccrualType.objects.all()
    serializer_class = AccrualTypeSerializer
    def get_queryset(self):
        queryset = super().get_queryset()
        sort_by = self.request.query_params.get('sort_by', 'name')
        return queryset.order_by(sort_by)

# ViewSet для Изображений
class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer

    def perform_create(self, serializer):
        image = self.request.FILES['image_file']
        image.name = transliterate_filename(image.name)  # Применяем транслитерацию к имени файла
        serializer.save(image_file=image)


# ViewSet для Товаров
class ProductPagination(PageNumberPagination):
    page_size = 20  # Количество записей на странице
    page_size_query_param = 'page_size'

# ================================
#  НОВЫЙ API ДЛЯ ТАБЛИЦЫ ТОВАРОВ
#  /api/products_table/
# ================================
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from cargo_acc.models import Product


@login_required
def products_table(request):
    """
    Универсальный API таблицы товаров:
    • tab: in_transit / delivered
    • fields: список полей через запятую
    • фильтры filter[field]=value
    • сортировка sort_by / sort_dir
    • пагинация offset / limit
    • контроль ролей: Клиент видит только свои товары
    """

    # -----------------------------
    # 1. ПАРАМЕТРЫ
    # -----------------------------
    tab = request.GET.get("tab", "").strip()

    try:
        limit = int(request.GET.get("limit", 50))
        offset = int(request.GET.get("offset", 0))
    except:
        return JsonResponse({"error": "bad pagination"}, status=400)

    sort_by = request.GET.get("sort_by", "id").strip()
    sort_dir = request.GET.get("sort_dir", "desc").strip()

    requested_fields = [
        f.strip() for f in request.GET.get("fields", "").split(",") if f.strip()
    ]

    # -----------------------------
    # 2. БАЗОВЫЙ QUERYSET
    # -----------------------------
    qs = Product.objects.select_related(
        "client", "company", "warehouse", "cargo_type",
        "cargo_status", "packaging_type"
    )

    # -----------------------------
    # 3. КОНТРОЛЬ РОЛЕЙ
    # -----------------------------
    user = request.user
    role = getattr(user, "role", "")

    if role == "Client":
        linked = getattr(user, "linked_client", None)
        if not linked:
            return JsonResponse({"results": [], "has_more": False, "total": 0})
        qs = qs.filter(client_id=linked.id)

    elif role in ["Admin", "Operator"]:
        pass  # видят всё

    else:
        return JsonResponse({"results": [], "has_more": False, "total": 0})

    # -----------------------------
    # 4. РАЗДЕЛЕНИЕ "В ПУТИ" / "ОТДАН"
    # -----------------------------
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

    # -----------------------------
    # 5. ФИЛЬТРАЦИЯ
    # -----------------------------
    for key, value in request.GET.items():
        if key.startswith("filter[") and key.endswith("]") and value.strip():
            field = key[7:-1]  # filter[field]
            qs = qs.filter(**{f"{field}__icontains": value.strip()})

    # -----------------------------
    # 6. СОРТИРОВКА
    # -----------------------------
    if sort_by:
        if sort_dir == "desc":
            sort_by = "-" + sort_by
        qs = qs.order_by(sort_by)

    # -----------------------------
    # 7. ПАГИНАЦИЯ
    # -----------------------------
    total = qs.count()
    qs = qs[offset:offset + limit]
    has_more = offset + limit < total

    # -----------------------------
    # 8. СПИСОК ВСЕХ ДОСТУПНЫХ ПОЛЕЙ
    # -----------------------------
    AVAILABLE_FIELDS = {
        # простые поля Product
        "id": "simple",
        "product_code": "simple",
        "cargo_description": "simple",
        "comment": "simple",
        "departure_place": "simple",
        "destination_place": "simple",
        "weight": "simple",
        "volume": "simple",
        "cost": "simple",
        "insurance": "simple",
        "delivery_time": "simple",
        "record_date": "date",
        "shipping_date": "date",
        "delivery_date": "date",
        "qr_code": "simple",
        "qr_created_at": "date",

        # связи
        "client": "related_client",
        "company": "related_company",
        "warehouse": "related_warehouse",
        "cargo_type": "related_cargo_type",
        "cargo_status": "related_cargo_status",
        "packaging_type": "related_packaging_type",
    }

    # -----------------------------
    # 9. РУСИФИЦИРОВАННОЕ ФОРМИРОВАНИЕ ОТВЕТА
    # -----------------------------

    # Маппинг: английское поле → русское название колонки
    RUS_LABELS = {
        "id": "ID",
        "product_code": "Код товара",
        "cargo_description": "Описание",
        "comment": "Комментарий",
        "departure_place": "Пункт отправления",
        "destination_place": "Пункт назначения",
        "weight": "Вес",
        "volume": "Объём",
        "cost": "Стоимость",
        "insurance": "Страховка",
        "delivery_time": "Срок доставки",
        "record_date": "Дата записи",
        "shipping_date": "Дата отправки",
        "delivery_date": "Дата доставки",
        "qr_code": "QR-код",
        "qr_created_at": "Дата QR",

        # связи
        "client": "Клиент",
        "company": "Компания",
        "warehouse": "Склад",
        "cargo_type": "Тип груза",
        "cargo_status": "Статус",
        "packaging_type": "Тип упаковки",
    }

    results = []

    for p in qs:
        row = {}

        for f in requested_fields:
            f_type = AVAILABLE_FIELDS.get(f)
            if not f_type:
                continue

            # ---- простые ----
            if f_type == "simple":
                val = getattr(p, f, "")

            # ---- даты ----
            elif f_type == "date":
                d = getattr(p, f, None)
                val = d.strftime("%d.%m.%Y") if d else ""

            # ---- связи ----
            elif f_type == "related_client":
                val = p.client.client_code if p.client else ""

            elif f_type == "related_company":
                val = p.company.name if p.company else ""

            elif f_type == "related_warehouse":
                val = p.warehouse.name if p.warehouse else ""

            elif f_type == "related_cargo_type":
                val = p.cargo_type.name if p.cargo_type else ""

            elif f_type == "related_cargo_status":
                val = p.cargo_status.name if p.cargo_status else ""

            elif f_type == "related_packaging_type":
                val = p.packaging_type.name if p.packaging_type else ""

            else:
                val = ""

            # -----------------------
            # Русифицированный ключ
            # -----------------------
            rus_key = RUS_LABELS.get(f, f)

            row[rus_key] = val

        results.append(row)

    return JsonResponse({
        "results": results,
        "has_more": has_more,
        "total": total
    })

