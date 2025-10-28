# File: cargo_acc/views.py

import json
import os
import time

import transliterate
from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage
from django.http import JsonResponse
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from .models import Client
from .models import Company, Warehouse, CargoType, CargoStatus, PackagingType, Image, Product, Cargo, \
    CarrierCompany, Vehicle, TransportBill, CargoMovement
from .serializers import CompanySerializer, ClientSerializer, WarehouseSerializer, CargoTypeSerializer, \
    CargoStatusSerializer, PackagingTypeSerializer, ImageSerializer, ProductSerializer, CargoSerializer, \
    CarrierCompanySerializer, VehicleSerializer, TransportBillSerializer, CargoMovementSerializer


# === HTML страницы ===
def settings_modal(request):
    return render(request, 'cargo_acc/settings_modal.html')


def client_table_page(request):
    """Отображение страницы с таблицей клиентов."""
    return render(request, 'cargo_acc/client_table.html')


def mod_addrow_view(request):
    return render(request, 'cargo_acc/mod_addrow.html')


def mod_delrow_view(request):
    return render(request, 'cargo_acc/mod_delrow.html')


def client_table_data(request):
    """API для выгрузки таблицы клиентов с фильтрацией и пагинацией."""
    try:
        # Фильтрация по параметру 'search' из GET-запроса
        search_query = request.GET.get('search', '').lower()
        clients = Client.objects.filter(client_code__icontains=search_query).select_related('company')

        # Пагинация
        paginator = Paginator(clients, 10)  # 10 записей на страницу
        page = request.GET.get('page', 1)
        try:
            clients_page = paginator.page(page)
        except EmptyPage:
            return JsonResponse({'results': [], 'page': page, 'total_pages': paginator.num_pages})

        # Формирование результата
        result = [
            {'id': client.id, 'client_code': client.client_code, 'company': client.company.name}
            for client in clients_page
        ]
        return JsonResponse({
            'results': result,
            'page': page,
            'total_pages': paginator.num_pages,
        })

    except Exception as e:
        # Логирование ошибки вместо print
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Ошибка: {e}")
        return JsonResponse({'error': str(e)}, status=500)


# === API справочники ===
@login_required
def get_clients(request):
    search_query = request.GET.get('search', '').lower()
    page = int(request.GET.get('page', 1))  # Параметр страницы
    page_size = int(request.GET.get('page_size', 7))  # Лимит записей

    clients = Client.objects.filter(client_code__icontains=search_query)
    paginator = Paginator(clients, page_size)

    try:
        clients_page = paginator.page(page)
    except EmptyPage:
        return JsonResponse({'results': [], 'error': 'Страница не существует'}, status=404)

    result = [{'id': c.id, 'client_code': c.client_code} for c in clients_page]
    return JsonResponse({
        'results': result,
        'page': page,
        'total_pages': paginator.num_pages,
    })


@login_required
def get_warehouses(request):
    search_query = request.GET.get('search', '').lower()
    warehouses = Warehouse.objects.filter(name__icontains=search_query).select_related('company')

    # Пагинация
    paginator = Paginator(warehouses, 10)
    page = request.GET.get('page', 1)
    try:
        warehouses_page = paginator.page(page)
    except EmptyPage:
        return JsonResponse({'results': [], 'page': page, 'total_pages': paginator.num_pages})

    result = [
        {'id': warehouse.id, 'name': warehouse.name, 'address': warehouse.address, 'company': warehouse.company.name}
        for warehouse in warehouses_page
    ]
    return JsonResponse({'results': result, 'page': page, 'total_pages': paginator.num_pages})


@login_required
def get_companies(request):
    search_query = request.GET.get('search', '').lower()
    companies = Company.objects.filter(name__icontains=search_query)

    # Пагинация
    paginator = Paginator(companies, 10)
    page = request.GET.get('page', 1)
    try:
        companies_page = paginator.page(page)
    except EmptyPage:
        return JsonResponse({'results': [], 'page': page, 'total_pages': paginator.num_pages})

    result = [
        {'id': company.id, 'name': company.name, 'registration': company.registration,
         'description': company.description}
        for company in companies_page
    ]
    return JsonResponse({'results': result, 'page': page, 'total_pages': paginator.num_pages})


@login_required
def get_cargo_types(request):
    search_query = request.GET.get('search', '').lower()
    cargo_types = CargoType.objects.filter(name__icontains=search_query)

    # Пагинация
    paginator = Paginator(cargo_types, 10)
    page = request.GET.get('page', 1)
    try:
        cargo_types_page = paginator.page(page)
    except EmptyPage:
        return JsonResponse({'results': [], 'page': page, 'total_pages': paginator.num_pages})

    result = [
        {'id': cargo_type.id, 'name': cargo_type.name, 'description': cargo_type.description}
        for cargo_type in cargo_types_page
    ]
    return JsonResponse({'results': result, 'page': page, 'total_pages': paginator.num_pages})


@login_required
def get_cargo_statuses(request):
    search_query = request.GET.get('search', '').lower()
    cargo_statuses = CargoStatus.objects.filter(name__icontains=search_query)

    # Пагинация
    paginator = Paginator(cargo_statuses, 10)
    page = request.GET.get('page', 1)
    try:
        cargo_statuses_page = paginator.page(page)
    except EmptyPage:
        return JsonResponse({'results': [], 'page': page, 'total_pages': paginator.num_pages})

    result = [
        {'id': cargo_status.id, 'name': cargo_status.name, 'description': cargo_status.description}
        for cargo_status in cargo_statuses_page
    ]
    return JsonResponse({'results': result, 'page': page, 'total_pages': paginator.num_pages})


@login_required
def get_packaging_types(request):
    search_query = request.GET.get('search', '').lower()
    packaging_types = PackagingType.objects.filter(name__icontains=search_query)

    # Пагинация
    paginator = Paginator(packaging_types, 10)
    page = request.GET.get('page', 1)
    try:
        packaging_types_page = paginator.page(page)
    except EmptyPage:
        return JsonResponse({'results': [], 'page': page, 'total_pages': paginator.num_pages})

    result = [
        {'id': packaging_type.id, 'name': packaging_type.name, 'description': packaging_type.description}
        for packaging_type in packaging_types_page
    ]
    return JsonResponse({'results': result, 'page': page, 'total_pages': paginator.num_pages})


def add_image_to_product(request, product_id):
    """API для загрузки картинки."""
    if request.method == 'POST' and request.FILES.get('image_file'):
        product = get_object_or_404(Product, id=product_id)

        # Создаем новое изображение и сохраняем его
        image = Image.objects.create(image_file=request.FILES['image_file'])

        # Добавляем это изображение к продукту
        product.images.add(image)

        return JsonResponse({
            'success': True,
            'image_url': image.image_file.url,
            'message': 'Изображение успешно добавлено!',
        })
    return JsonResponse({'success': False, 'message': 'Ошибка при добавлении изображения.'}, status=400)


def transliterate_filename(filename):
    """API для записи латиницей."""
    name, ext = os.path.splitext(filename)
    # Транслитерация имени файла с кириллицы на латиницу
    return transliterate.translit(name, 'ru', reversed=True) + ext


# === API проверки ===
# Проверка уникальности названия типа упаковки
def check_packaging_type_name(request):
    """API для проверки уникальности названия типа упаковки."""
    packaging_type_name = request.GET.get('name', '')
    is_unique = not PackagingType.objects.filter(name=packaging_type_name).exists()
    return JsonResponse({'is_unique': is_unique})


# Проверка уникальности названия статуса груза
def check_cargo_status_name(request):
    """API для проверки уникальности названия статуса груза."""
    cargo_status_name = request.GET.get('name', '')
    is_unique = not CargoStatus.objects.filter(name=cargo_status_name).exists()
    return JsonResponse({'is_unique': is_unique})


# Проверка уникальности названия типа груза
def check_cargo_type_name(request):
    """API для проверки уникальности названия типа груза."""
    cargo_type_name = request.GET.get('name', '')
    is_unique = not CargoType.objects.filter(name=cargo_type_name).exists()
    return JsonResponse({'is_unique': is_unique})


def check_client_code(request):
    """API для проверки уникальности названия Клиента."""
    client_code = request.GET.get('client_code', '')
    is_unique = not Client.objects.filter(client_code=client_code).exists()
    return JsonResponse({'is_unique': is_unique})


def check_company_name(request):
    """API для проверки уникальности названия Компании."""
    company_name = request.GET.get('name', '')
    is_unique = not Company.objects.filter(name=company_name).exists()
    return JsonResponse({'is_unique': is_unique})


def check_warehouse_name(request):
    """API для проверки уникальности названия Склада."""
    warehouse_name = request.GET.get('name', '')
    is_unique = not Warehouse.objects.filter(name=warehouse_name).exists()
    return JsonResponse({'is_unique': is_unique})


@login_required
def add_client(request):
    """API для добавления клиента."""
    if request.method == 'POST':
        try:
            # Чтение данных из запроса
            data = json.loads(request.body)
            client_code = data.get('client_code')
            company_name = data.get('company')
            description = data.get('description')

            # Поиск или создание компании
            company, created = Company.objects.get_or_create(name=company_name)

            # Создание клиента с компанией
            client = Client.objects.create(
                client_code=client_code,
                company=company,  # Ссылка на объект компании
                description=description
            )

            return JsonResponse({'message': 'Client created successfully', 'client_id': client.id}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


# Вьюшка для загрузки настроек таблицы
@login_required
def get_table_settings(request):
    user = request.user
    return JsonResponse(user.table_settings or {})


# Вьюшка для сохранения настроек таблицы
@csrf_exempt
@login_required
def save_table_settings(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=400)

    try:
        data = json.loads(request.body)
        user = request.user
        settings = user.table_settings or {}  # не затираем существующие
        settings.update(data)                 # добавляем/обновляем конкретную таблицу
        user.table_settings = settings
        user.save(update_fields=["table_settings"])
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


class UniversalDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, model_name, pk):
        try:
            # Динамически получаем модель по имени
            model = apps.get_model('cargo_acc', model_name)
            # Пытаемся найти запись по ID
            instance = model.objects.get(pk=pk)
            instance.delete()  # Удаляем запись
            return JsonResponse({'message': 'Запись успешно удалена'}, status=status.HTTP_204_NO_CONTENT)
        except model.DoesNotExist:
            return JsonResponse({'error': 'Запись не найдена'}, status=status.HTTP_404_NOT_FOUND)
        except LookupError:
            return JsonResponse({'error': 'Модель не найдена'}, status=status.HTTP_400_BAD_REQUEST)


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

from django.contrib.auth.decorators import login_required

@login_required
def operator_clients(request):
    """Страница справочника клиентов и внесения платежей (для оператора)."""
    return render(request, 'cargo_acc/operator_clients.html')

# Класс `ProductViewSet` является часть DRF (Django Rest Framework) и предоставляет API-интерфейс для работы с моделью `Product`. Он наследует от `ModelViewSet`, который предоставляет ряд стандартных действий, таких как создание, обновление, удаление и получение объектов.
#
# ### Основные компоненты и назначение:
#
# 1. **QuerySet:**
#    - Используется `select_related` для выборки связанных объектов `client`, `company`, `warehouse`, `cargo_type`, `cargo_status`, и `packaging_type`, что оптимизирует запросы, выполняя SQL JOIN. Это позволяет избежать N+1 проблемы при обращении к связанным данным.
#    - `prefetch_related` применяется для поля `images`, что оптимизирует выборку объектов с ManyToMany отношениями, кэшируя связанные объекты в отдельном запросе.
#
# 2. **Serializer:**
#    - `serializer_class = ProductSerializer` указывает на сериализатор, который будет использоваться для преобразования объектов `Product` в JSON и обратно.
#
# 3. **HTTP методы:**
#    - `http_method_names` перечисляет методы, которые поддерживает данный ViewSet. Это стандартный набор методов для REST API: получение, создание, полное и частичное обновление, удаление, а также обработка заголовков.
#
# 4. **Метод `list`:**
#    - Этот метод обрабатывает GET-запросы для получения списка продуктов.
#    - **Пагинация:** Сначала проверяется, поддерживает ли запрос пагинацию. Если да, продукция будет разбита на страницы, чтобы уменьшить нагрузку на сервер и клиент.
#    - **Сериализация:** Объекты сериализуются в JSON-формат и отправляются обратно в виде HTTP-ответа.
#    - Метод `list` переопределяется, чтобы убедиться, что используется весь QuerySet без вызова `values()`, что сохраняет полную структуру объектов при сериализации.
#
# ### Общий API функционал:
#
# - **GET** `/products/`: Получает список всех продуктов.
# - **POST** `/products/`: Создает новый продукт.
# - **PUT/PATCH** `/products/{id}/`: Обновляет указанный продукт.
# - **DELETE** `/products/{id}/`: Удаляет указанный продукт.
#
# Это ViewSet обеспечивает CRUD функционал для модели `Product` в рамках RESTful API, позволяя клиентам осуществлять операции с учетными записями продуктов с помощью отправки HTTP-запросов.
class ProductViewSet(ModelViewSet):
    queryset = Product.objects.select_related(
        'client', 'company', 'warehouse', 'cargo_type', 'cargo_status', 'packaging_type'
    ).prefetch_related('images')
    serializer_class = ProductSerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']

    def list(self, request, *args, **kwargs):
        # Возвращаем QuerySet без использования values()
        queryset = self.queryset.all()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# ViewSet для Грузов
class CargoViewSet(viewsets.ModelViewSet):
    queryset = Cargo.objects.all()
    serializer_class = CargoSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        sort_by = self.request.query_params.get('sort_by', 'id')
        return queryset.order_by(sort_by)


# ViewSet для Компаний-Перевозчиков
class CarrierCompanyViewSet(viewsets.ModelViewSet):
    queryset = CarrierCompany.objects.all()
    serializer_class = CarrierCompanySerializer

    def get_queryset(self):
        queryset = super().get_queryset()  # Получаем первоначальный queryset из родительского метода
        sort_by = self.request.query_params.get('sort_by', 'name')  # Получаем параметр для сортировки из запроса
        return queryset.order_by(sort_by)  # Сортируем по переданному полю (по умолчанию 'name')


# ViewSet для Автомобилей
class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer

    def get_queryset(self):
        queryset = super().get_queryset()  # Получаем первоначальный queryset из родительского метода
        sort_by = self.request.query_params.get('sort_by',
                                                'license_plate')  # Получаем параметр для сортировки из запроса
        return queryset.order_by(sort_by)  # Сортируем по переданному полю (по умолчанию 'name')


# ViewSet для Транспортных Накладных
class TransportBillViewSet(viewsets.ModelViewSet):
    queryset = TransportBill.objects.all()
    serializer_class = TransportBillSerializer

    def get_queryset(self):
        queryset = super().get_queryset()  # Получаем первоначальный queryset из родительского метода
        sort_by = self.request.query_params.get('sort_by', 'bill_code')  # Получаем параметр для сортировки из запроса
        return queryset.order_by(sort_by)  # Сортируем по переданному полю (по умолчанию 'name')


# ViewSet для Перемещений Грузов
class CargoMovementViewSet(viewsets.ModelViewSet):
    queryset = CargoMovement.objects.all()
    serializer_class = CargoMovementSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        sort_by = self.request.query_params.get('sort_by', 'id')  # ← заменить name на id
        return queryset.order_by(sort_by)


# === SSE поток ===
last_update_timestamp = time.time()


# Функция `mark_clients_changed` служит для обновления временной метки, указывающей на то, что данные о клиентах были изменены.
def mark_clients_changed():
    global last_update_timestamp
    last_update_timestamp = time.time()


# Функция `sse_clients_stream` предназначена для передачи данных о клиентах в режиме реального времени через серверную отправку событий (Server-Sent Events, SSE)
def sse_clients_stream(request):
    def event_stream():
        local_ts = 0
        while True:
            if last_update_timestamp > local_ts:
                data = list(Client.objects.values('id', 'client_code', 'description'))
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                local_ts = last_update_timestamp
            time.sleep(30)

    return StreamingHttpResponse(event_stream(), content_type='text/event-stream')
