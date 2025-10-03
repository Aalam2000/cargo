import os
import django
import random
import decimal
from django.utils import timezone
from django.core.management.base import BaseCommand
from cargo_acc.models import (
    Company, Client, Warehouse, CargoType, CargoStatus, PackagingType, Product
)

# Указываем настройки проекта Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cargodb.settings')
django.setup()

class Command(BaseCommand):
    help = 'Добавляет 20 тестовых строк в таблицу Product.'

    def handle(self, *args, **kwargs):
        # Получаем существующие данные из связанных таблиц
        companies = Company.objects.all()
        clients = Client.objects.all()
        warehouses = Warehouse.objects.all()
        cargo_types = CargoType.objects.all()
        cargo_statuses = CargoStatus.objects.all()
        packaging_types = PackagingType.objects.all()

        # Проверяем, достаточно ли данных для заполнения
        if not (companies and clients and warehouses and cargo_types and cargo_statuses and packaging_types):
            self.stdout.write(self.style.ERROR('Недостаточно данных в связанных таблицах. Проверьте наличие записей.'))
            return

        # Генерация данных для добавления в таблицу Product
        existing_codes = set(Product.objects.values_list('product_code', flat=True))
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
                'weight': decimal.Decimal(random.uniform(1, 50)).quantize(decimal.Decimal('0.01')),
                'volume': decimal.Decimal(random.uniform(0.1, 10)).quantize(decimal.Decimal('0.01')),
                'cost': decimal.Decimal(random.uniform(10, 500)).quantize(decimal.Decimal('0.01')),
                'insurance': decimal.Decimal(random.uniform(1, 50)).quantize(decimal.Decimal('0.01')),
                'dimensions': f"{random.randint(10, 100)}x{random.randint(10, 100)}x{random.randint(10, 100)}",
                'shipping_date': timezone.now(),
                'delivery_date': timezone.now() + timezone.timedelta(days=random.randint(1, 10)),
                'cargo_status': random.choice(cargo_statuses),
                'packaging_type': random.choice(packaging_types),
                'delivery_time': decimal.Decimal(random.uniform(1, 5)).quantize(decimal.Decimal('0.01'))
            }
            for i in range(20) if f'Товар {i}' not in existing_codes
        ]

        # Добавление записей в базу данных
        for entry in product_data:
            Product.objects.create(**entry)
            self.stdout.write(self.style.SUCCESS(f'Добавлена запись: {entry["product_code"]}'))

        self.stdout.write(self.style.SUCCESS(f'Добавлено {len(product_data)} записей в таблицу Product.'))
