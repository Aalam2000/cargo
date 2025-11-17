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
    CarrierCompanySerializer, VehicleSerializer, TransportBillSerializer, CargoMovementSerializer
from .models import Company, Warehouse, CargoType, CargoStatus, PackagingType, Image, Product, Cargo, \
    CarrierCompany, Vehicle, TransportBill, CargoMovement, Client



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
