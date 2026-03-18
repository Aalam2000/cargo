# cargo_acc/views.py
import json
import logging
import os
import sys
import time
import traceback

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
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from .models import Company, Warehouse, CargoType, CargoStatus, PackagingType, Image, Product, Cargo, \
    CarrierCompany, Vehicle, TransportBill, CargoMovement, Client
from .serializers import ProductSerializer, CargoSerializer, \
    CarrierCompanySerializer, VehicleSerializer, TransportBillSerializer, CargoMovementSerializer

logger = logging.getLogger(__name__)


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
        search_query = request.GET.get('search', '').lower()
        clients = Client.objects.filter(
            company=request.company,
            client_code__icontains=search_query
        ).select_related('company')

        paginator = Paginator(clients, 10)
        page = request.GET.get('page', 1)
        try:
            clients_page = paginator.page(page)
        except EmptyPage:
            return JsonResponse({'results': [], 'page': page, 'total_pages': paginator.num_pages})

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
        logger.error(f"Ошибка: {e}")
        return JsonResponse({'error': str(e)}, status=500)


# === API справочники ===
@login_required
def get_clients(request):
    search_query = request.GET.get('search', '').lower()
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 7))

    clients = Client.objects.filter(
        company=request.company,
        client_code__icontains=search_query
    ).order_by('client_code')
    paginator = Paginator(clients, page_size)

    try:
        clients_page = paginator.page(page)
    except EmptyPage:
        return JsonResponse({'results': [], 'error': 'Страница не существует'}, status=404)

    result = [
        {
            'id': c.id,
            'client_code': c.client_code,
            'company': c.company.name,
            'description': c.description,
        }
        for c in clients_page
    ]
    return JsonResponse({
        'results': result,
        'page': page,
        'total_pages': paginator.num_pages,
    })


@login_required
def get_companies(request):
    search_query = request.GET.get('search', '').lower()
    companies = Company.objects.filter(
        id=request.company.id,
        name__icontains=search_query
    )

    paginator = Paginator(companies, 10)
    page = request.GET.get('page', 1)
    try:
        companies_page = paginator.page(page)
    except EmptyPage:
        return JsonResponse({'results': [], 'page': page, 'total_pages': paginator.num_pages})

    result = [
        {
            'id': company.id,
            'name': company.name,
            'registration': company.registration,
            'description': company.description,
        }
        for company in companies_page
    ]
    return JsonResponse({'results': result, 'page': page, 'total_pages': paginator.num_pages})


def add_image_to_product(request, product_id):
    """API для загрузки картинки."""
    if request.method == 'POST' and request.FILES.get('image_file'):
        product = get_object_or_404(Product, id=product_id, company=request.company)

        image = Image.objects.create(image_file=request.FILES['image_file'])
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
    is_unique = not PackagingType.objects.filter(
        company=request.company,
        name=packaging_type_name
    ).exists()
    return JsonResponse({'is_unique': is_unique})


# Проверка уникальности названия статуса груза
def check_cargo_status_name(request):
    """API для проверки уникальности названия статуса груза."""
    cargo_status_name = request.GET.get('name', '')
    is_unique = not CargoStatus.objects.filter(
        company=request.company,
        name=cargo_status_name
    ).exists()
    return JsonResponse({'is_unique': is_unique})


# Проверка уникальности названия типа груза
def check_cargo_type_name(request):
    """API для проверки уникальности названия типа груза."""
    cargo_type_name = request.GET.get('name', '')
    is_unique = not CargoType.objects.filter(
        company=request.company,
        name=cargo_type_name
    ).exists()
    return JsonResponse({'is_unique': is_unique})


def check_client_code(request):
    """API для проверки уникальности названия Клиента."""
    client_code = request.GET.get('client_code', '')
    is_unique = not Client.objects.filter(
        company=request.company,
        client_code=client_code
    ).exists()
    return JsonResponse({'is_unique': is_unique})


def check_company_name(request):
    """API для проверки уникальности названия Компании."""
    company_name = request.GET.get('name', '')
    is_unique = not Company.objects.filter(
        id=request.company.id,
        name=company_name
    ).exists()
    return JsonResponse({'is_unique': is_unique})


def check_warehouse_name(request):
    """API для проверки уникальности названия Склада."""
    warehouse_name = request.GET.get('name', '')
    is_unique = not Warehouse.objects.filter(
        company=request.company,
        name=warehouse_name
    ).exists()
    return JsonResponse({'is_unique': is_unique})


@login_required
def add_client(request):
    """API для добавления клиента."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    try:
        data = json.loads(request.body)
        client_code = data.get('client_code')
        description = data.get('description')

        client = Client.objects.create(
            client_code=client_code,
            company=request.company,
            description=description
        )

        return JsonResponse(
            {'message': 'Client created successfully', 'client_id': client.id},
            status=201
        )
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


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
        settings.update(data)  # добавляем/обновляем конкретную таблицу
        user.table_settings = settings
        user.save(update_fields=["table_settings"])
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


class UniversalDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, model_name, pk):
        try:
            model = apps.get_model('cargo_acc', model_name)

            if not hasattr(model, 'company'):
                return JsonResponse(
                    {'error': 'Удаление для этой модели не поддерживается'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            instance = model.objects.get(pk=pk, company=request.company)
            instance.delete()
            return JsonResponse(
                {'message': 'Запись успешно удалена'},
                status=status.HTTP_204_NO_CONTENT
            )

        except LookupError:
            return JsonResponse(
                {'error': 'Модель не найдена'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except model.DoesNotExist:
            return JsonResponse(
                {'error': 'Запись не найдена'},
                status=status.HTTP_404_NOT_FOUND
            )


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

    def get_queryset(self):
        return self.queryset.filter(company=self.request.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.company)

    def list(self, request, *args, **kwargs):
        try:
            print("+++ ProductViewSet.list START user:", getattr(request, "user", None), file=sys.stderr)

            queryset = self.get_queryset()

            try:
                print("+++ ProductViewSet queryset SQL:", str(queryset.query), file=sys.stderr)
            except Exception as e_q:
                print("+++ ProductViewSet: cannot read queryset.query:", e_q, file=sys.stderr)

            try:
                cnt = queryset.count()
                print("+++ ProductViewSet queryset.count():", cnt, file=sys.stderr)
            except Exception as e_cnt:
                print("+++ ProductViewSet: queryset.count() error:", e_cnt, file=sys.stderr)

            page = self.paginate_queryset(queryset)
            if page is not None:
                print("+++ ProductViewSet: using pagination, page length:", len(page), file=sys.stderr)
                serializer = self.get_serializer(page, many=True)
                print("+++ ProductViewSet: serializer created for page", file=sys.stderr)
                return self.get_paginated_response(serializer.data)

            print("+++ ProductViewSet: serializing full queryset", file=sys.stderr)
            serializer = self.get_serializer(queryset, many=True)

            try:
                items_len = len(serializer.data)
            except Exception as e_ser:
                items_len = f"error getting len: {e_ser}"
            print("+++ ProductViewSet: serialization finished, items:", items_len, file=sys.stderr)

            return Response(serializer.data)

        except Exception as e:
            tb = traceback.format_exc()
            print("=== ProductViewSet.list EXCEPTION ===", file=sys.stderr)
            print(tb, file=sys.stderr)
            for _n in ('debug', 'pol'):
                __import__('logging').getLogger(_n).exception("ProductViewSet.list error", exc_info=True)
            return Response({"error": str(e), "traceback": tb}, status=500)


# ViewSet для Грузов
class CargoViewSet(viewsets.ModelViewSet):
    queryset = Cargo.objects.all()
    serializer_class = CargoSerializer

    def get_queryset(self):
        queryset = super().get_queryset().filter(company=self.request.company)
        sort_by = self.request.query_params.get('sort_by', 'id')
        return queryset.order_by(sort_by)


# ViewSet для Компаний-Перевозчиков
class CarrierCompanyViewSet(viewsets.ModelViewSet):
    queryset = CarrierCompany.objects.all()
    serializer_class = CarrierCompanySerializer

    def get_queryset(self):
        queryset = super().get_queryset().filter(company=self.request.company)
        sort_by = self.request.query_params.get('sort_by', 'name')
        return queryset.order_by(sort_by)


# ViewSet для Автомобилей
class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer

    def get_queryset(self):
        queryset = super().get_queryset().filter(company=self.request.company)
        sort_by = self.request.query_params.get('sort_by', 'license_plate')
        return queryset.order_by(sort_by)


# ViewSet для Транспортных Накладных
class TransportBillViewSet(viewsets.ModelViewSet):
    queryset = TransportBill.objects.all()
    serializer_class = TransportBillSerializer

    def get_queryset(self):
        queryset = super().get_queryset().filter(company=self.request.company)
        sort_by = self.request.query_params.get('sort_by', 'bill_code')
        return queryset.order_by(sort_by)


# ViewSet для Перемещений Грузов
class CargoMovementViewSet(viewsets.ModelViewSet):
    queryset = CargoMovement.objects.all()
    serializer_class = CargoMovementSerializer

    def get_queryset(self):
        queryset = super().get_queryset().filter(company=self.request.company)
        sort_by = self.request.query_params.get('sort_by', 'id')
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
                data = list(
                    Client.objects.filter(company=request.company).values(
                        'id', 'client_code', 'description'
                    )
                )
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                local_ts = last_update_timestamp
            time.sleep(30)

    return StreamingHttpResponse(event_stream(), content_type='text/event-stream')


@login_required
def references_page(request):
    return render(request, 'cargo_acc/references.html', {
        "company_id": request.user.company.id,
        "company_name": request.user.company.name
    })


@login_required
def products_page(request):
    return render(request, "cargo_acc/product_table.html")
