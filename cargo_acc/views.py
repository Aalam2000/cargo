import os
import transliterate
import json
from django.apps import apps
from rest_framework import status
from rest_framework.views import APIView
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets

from .models import Company, Client, Warehouse, CargoType, CargoStatus, PackagingType, Image, Product, Cargo, \
    CarrierCompany, Vehicle, TransportBill, CargoMovement
from .serializers import CompanySerializer, ClientSerializer, WarehouseSerializer, CargoTypeSerializer, \
    CargoStatusSerializer, PackagingTypeSerializer, ImageSerializer, ProductSerializer, CargoSerializer, \
    CarrierCompanySerializer, VehicleSerializer, TransportBillSerializer, CargoMovementSerializer


def client_table_page(request):
    """Отображение страницы с таблицей клиентов."""
    return render(request, 'cargo_acc/client_table.html')


def client_table_data(request):
    """API для выгрузки всей таблицы клиентов."""
    try:
        clients = Client.objects.select_related('company').order_by('id')
        serializer = ClientSerializer(clients, many=True)
        return JsonResponse({'results': serializer.data})

    except Exception as e:
        print(f"Ошибка: {e}")
        return JsonResponse({'error': str(e)}, status=500)


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


@csrf_exempt
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
    if request.method == 'POST':
        data = json.loads(request.body)
        request.user.table_settings = data
        request.user.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)


class UniversalDeleteView(APIView):
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
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_queryset(self):
        queryset = super().get_queryset()  # Получаем первоначальный queryset из родительского метода
        sort_by = self.request.query_params.get('sort_by',
                                                'product_code')  # Получаем параметр для сортировки из запроса
        return queryset.order_by(sort_by)  # Сортируем по переданному полю (по умолчанию 'name')


# ViewSet для Грузов
class CargoViewSet(viewsets.ModelViewSet):
    queryset = Cargo.objects.all()
    serializer_class = CargoSerializer

    def get_queryset(self):
        queryset = super().get_queryset()  # Получаем первоначальный queryset из родительского метода
        sort_by = self.request.query_params.get('sort_by', 'name')  # Получаем параметр для сортировки из запроса
        return queryset.order_by(sort_by)  # Сортируем по переданному полю (по умолчанию 'name')


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
        sort_by = self.request.query_params.get('sort_by', 'name')  # Получаем параметр для сортировки из запроса
        return queryset.order_by(sort_by)  # Сортируем по переданному полю (по умолчанию 'name')


# ViewSet для Транспортных Накладных
class TransportBillViewSet(viewsets.ModelViewSet):
    queryset = TransportBill.objects.all()
    serializer_class = TransportBillSerializer

    def get_queryset(self):
        queryset = super().get_queryset()  # Получаем первоначальный queryset из родительского метода
        sort_by = self.request.query_params.get('sort_by', 'name')  # Получаем параметр для сортировки из запроса
        return queryset.order_by(sort_by)  # Сортируем по переданному полю (по умолчанию 'name')


# ViewSet для Перемещений Грузов
class CargoMovementViewSet(viewsets.ModelViewSet):
    queryset = CargoMovement.objects.all()
    serializer_class = CargoMovementSerializer

    def get_queryset(self):
        queryset = super().get_queryset()  # Получаем первоначальный queryset из родительского метода
        sort_by = self.request.query_params.get('sort_by', 'name')  # Получаем параметр для сортировки из запроса
        return queryset.order_by(sort_by)  # Сортируем по переданному полю (по умолчанию 'name')
