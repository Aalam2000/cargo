import os
import django
import random
import decimal
from django.utils import timezone
from django.core.management.base import BaseCommand
from cargo_acc.models import (
    Company, Client, Warehouse, CargoType, CargoStatus, PackagingType,
    Image, Product, Cargo, CarrierCompany, Vehicle, TransportBill, CargoMovement
)

# Указываем настройки проекта Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cargodb.settings')
django.setup()

class Command(BaseCommand):
    help = 'Заполняет базу данных начальными значениями.'

    def add_entries(self, model, data, unique_field=None, unique_fields=None):
        """
        Добавляет записи в таблицу, если их ещё нет.
        model: модель Django для заполнения.
        data: список словарей с данными для заполнения.
        unique_field: поле для проверки уникальности (если одно).
        unique_fields: список полей для проверки уникальности (если несколько).
        """
        for entry_data in data:
            if unique_field:
                if not model.objects.filter(**{unique_field: entry_data[unique_field]}).exists():
                    model.objects.create(**entry_data)
                    self.stdout.write(self.style.SUCCESS(f'Добавлена запись: {entry_data[unique_field]}'))
            elif unique_fields:
                filter_params = {field: entry_data[field] for field in unique_fields}
                if not model.objects.filter(**filter_params).exists():
                    model.objects.create(**entry_data)
                    self.stdout.write(self.style.SUCCESS(f'Добавлена запись с уникальными полями: {filter_params}'))

    def handle(self, *args, **kwargs):
        # Компании
        company_data = [{'name': f'Компания {i}', 'registration': 'RU', 'description': f'Описание компании {i}'} for i in range(5)]
        self.add_entries(Company, company_data, 'name')

        # Клиенты
        companies = Company.objects.all()[:5]
        client_data = [{'client_code': f'Клиент {i}', 'company': random.choice(companies), 'description': f'Описание клиента {i}'} for i in range(5)]
        self.add_entries(Client, client_data, 'client_code')

        # Склады
        warehouse_data = [{'name': f'Склад {i}', 'address': f'Адрес склада {i}', 'company': random.choice(companies)} for i in range(5)]
        self.add_entries(Warehouse, warehouse_data, 'name')

        # Типы груза
        cargo_type_data = [{'name': f'Тип груза {i}', 'description': f'Описание типа {i}'} for i in range(5)]
        self.add_entries(CargoType, cargo_type_data, 'name')

        # Статусы груза
        cargo_status_data = [{'name': f'Статус {i}', 'description': f'Описание статуса {i}'} for i in range(5)]
        self.add_entries(CargoStatus, cargo_status_data, 'name')

        # Типы упаковок
        packaging_type_data = [{'name': f'Упаковка {i}', 'description': f'Описание упаковки {i}'} for i in range(5)]
        self.add_entries(PackagingType, packaging_type_data, 'name')

        # Изображения
        image_data = [{'image_file': f'img/image_{i}.jpg'} for i in range(5)]
        self.add_entries(Image, image_data, 'image_file')

        # Товары
        clients = Client.objects.all()[:5]
        warehouses = Warehouse.objects.all()[:5]
        cargo_types = CargoType.objects.all()[:5]
        cargo_statuses = CargoStatus.objects.all()[:5]
        packaging_types = PackagingType.objects.all()[:5]
        product_data = [
            {
                'client': random.choice(clients),
                'product_code': f'Товар {i}',
                'company': random.choice(companies),
                'warehouse': random.choice(warehouses),
                'record_date': timezone.now(),
                'cargo_description': f'Описание товара {i}',
                'cargo_type': random.choice(cargo_types),
                'departure_place': f'Место отправления {i}',
                'destination_place': f'Место назначения {i}',
                'weight': decimal.Decimal('10.00'),
                'volume': decimal.Decimal('5.00'),
                'cost': decimal.Decimal('100.00'),
                'insurance': decimal.Decimal('10.00'),
                'dimensions': "50x50x50",
                'shipping_date': timezone.now(),
                'delivery_date': timezone.now(),
                'cargo_status': random.choice(cargo_statuses),
                'packaging_type': random.choice(packaging_types),
                'delivery_time': decimal.Decimal('3.00')
            }
            for i in range(5)
        ]
        self.add_entries(Product, product_data, 'product_code')

        # Грузы
        products = Product.objects.all()[:5]
        cargo_data = [
            {
                'client': random.choice(clients),
                'cargo_code': f'Груз {i}',
                'departure_place': f'Отправка {i}',
                'destination_place': f'Назначение {i}',
                'weight': decimal.Decimal('20.00'),
                'volume': decimal.Decimal('10.00'),
                'cost': decimal.Decimal('200.00'),
                'insurance': decimal.Decimal('20.00'),
                'dimensions': "100x100x100",
                'shipping_date': timezone.now(),
                'delivery_date': timezone.now(),
                'cargo_status': random.choice(cargo_statuses),
                'packaging_type': random.choice(packaging_types),
                'delivery_time': decimal.Decimal('5.00')
            }
            for i in range(5)
        ]
        self.add_entries(Cargo, cargo_data, 'cargo_code')

        # Компании-перевозчики
        carrier_company_data = [{'name': f'Перевозчик {i}', 'registration': 'RU', 'description': f'Описание перевозчика {i}'} for i in range(5)]
        self.add_entries(CarrierCompany, carrier_company_data, 'name')

        # Автомобили
        carrier_companies = CarrierCompany.objects.all()[:5]
        vehicle_data = [{'license_plate': f'А{i}БВ77', 'model': f'Модель {i}', 'carrier_company': random.choice(carrier_companies), 'current_status': 'В пути'} for i in range(5)]
        self.add_entries(Vehicle, vehicle_data, 'license_plate')

        # Транспортные накладные
        cargos = Cargo.objects.all()[:5]
        vehicles = Vehicle.objects.all()[:5]
        transport_bill_data = [
            {
                'bill_code': f'Накладная {i}',
                'vehicle': random.choice(vehicles),
                'departure_place': f'Отправка накладная {i}',
                'destination_place': f'Назначение накладная {i}',
                'departure_date': timezone.now(),
                'arrival_date': timezone.now(),
                'carrier_company': random.choice(carrier_companies)
            }
            for i in range(5)
        ]
        self.add_entries(TransportBill, transport_bill_data, 'bill_code')

        # Перемещения грузов
        transport_bills = TransportBill.objects.all()[:5]
        cargo_movement_data = [
            {
                'cargo': random.choice(cargos),
                'from_transport_bill': random.choice(transport_bills),
                'to_transport_bill': random.choice(transport_bills),
                'transfer_place': f'Пункт перемещения {i}',
                'transfer_date': timezone.now()
            }
            for i in range(5)
        ]
        self.add_entries(CargoMovement, cargo_movement_data, unique_fields=['cargo', 'from_transport_bill', 'to_transport_bill'])
