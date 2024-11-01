from django.core.management.base import BaseCommand
from cargo_acc.models import (
    Company, Client, Warehouse, CargoType, CargoStatus, PackagingType,
    Image, Product, Cargo, CarrierCompany, Vehicle, TransportBill, CargoMovement
)
from django.utils import timezone
import random
import decimal

class Command(BaseCommand):
    help = 'Заполняет базу данных начальными значениями.'

    def handle(self, *args, **kwargs):
        # Заполнение таблицы Компании
        company = Company.objects.create(
            name="Наша компания",
            registration="Россия",
            description="Описание компании"
        )
        self.stdout.write(self.style.SUCCESS('Добавлена компания: Наша компания'))

        # Заполнение таблицы Клиенты
        client = Client.objects.create(
            client_code="НашКлиент",
            company=company,
            description="Описание нашего клиента"
        )
        self.stdout.write(self.style.SUCCESS('Добавлен клиент: Наш клиент'))

        # Заполнение таблицы Склады
        warehouse = Warehouse.objects.create(
            name="Наш склад",
            address="Адрес нашего склада",
            company=company
        )
        self.stdout.write(self.style.SUCCESS('Добавлен склад: Наш склад'))

        # Заполнение таблицы Типы груза
        cargo_type = CargoType.objects.create(
            name="Тип груза",
            description="Описание типа груза"
        )
        self.stdout.write(self.style.SUCCESS('Добавлен тип груза: Тип груза'))

        # Заполнение таблицы Статусы груза
        cargo_status = CargoStatus.objects.create(
            name="Статус груза",
            description="Описание статуса груза"
        )
        self.stdout.write(self.style.SUCCESS('Добавлен статус груза: Статус груза'))

        # Заполнение таблицы Типы упаковок
        packaging_type = PackagingType.objects.create(
            name="Тип упаковки",
            description="Описание типа упаковки"
        )
        self.stdout.write(self.style.SUCCESS('Добавлен тип упаковки: Тип упаковки'))

        # Заполнение таблицы Изображения
        image = Image.objects.create(
            image_file='img/default_image.jpg'  # Изменено на image_file
        )
        self.stdout.write(self.style.SUCCESS('Добавлено изображение: default.png'))

        # Заполнение таблицы Товары
        product = Product.objects.create(
            client=client,
            product_code="НашТовар",
            company=company,
            warehouse=warehouse,
            record_date=timezone.now(),
            cargo_description="Описание нашего товара",
            cargo_type=cargo_type,
            departure_place="Место отправления",
            destination_place="Место назначения",
            weight=decimal.Decimal('10.00'),
            volume=decimal.Decimal('5.00'),
            cost=decimal.Decimal('100.00'),
            insurance=decimal.Decimal('10.00'),
            dimensions="50x50x50",
            shipping_date=timezone.now(),
            delivery_date=timezone.now(),
            cargo_status=cargo_status,
            packaging_type=packaging_type,
            delivery_time=decimal.Decimal('3.00')
        )
        product.images.add(image)
        self.stdout.write(self.style.SUCCESS('Добавлен товар: Наш товар'))

        # Заполнение таблицы Грузы
        cargo = Cargo.objects.create(
            client=client,
            cargo_code="НашГруз",
            departure_place="Место отправления груза",
            destination_place="Место назначения груза",
            weight=decimal.Decimal('20.00'),
            volume=decimal.Decimal('10.00'),
            cost=decimal.Decimal('200.00'),
            insurance=decimal.Decimal('20.00'),
            dimensions="100x100x100",
            shipping_date=timezone.now(),
            delivery_date=timezone.now(),
            cargo_status=cargo_status,
            packaging_type=packaging_type,
            delivery_time=decimal.Decimal('5.00')
        )
        cargo.products.add(product)
        cargo.images.add(image)
        self.stdout.write(self.style.SUCCESS('Добавлен груз: Наш груз'))

        # Заполнение таблицы Компании-перевозчики
        carrier_company = CarrierCompany.objects.create(
            name="Наша компания перевозчик",
            registration="Россия",
            description="Описание перевозчика"
        )
        self.stdout.write(self.style.SUCCESS('Добавлена компания перевозчик: Наша компания перевозчик'))

        # Заполнение таблицы Автомобили
        vehicle = Vehicle.objects.create(
            license_plate="А123БВ77",
            model="Модель автомобиля",
            carrier_company=carrier_company,
            current_status="В пути"
        )
        self.stdout.write(self.style.SUCCESS('Добавлен автомобиль: А123БВ77'))

        # Заполнение таблицы Транспортные накладные
        transport_bill = TransportBill.objects.create(
            bill_code="Накладная001",
            vehicle=vehicle,
            departure_place="Место отправления накладной",
            destination_place="Место назначения накладной",
            departure_date=timezone.now(),
            arrival_date=timezone.now(),
            carrier_company=carrier_company
        )
        transport_bill.cargos.add(cargo)
        self.stdout.write(self.style.SUCCESS('Добавлена транспортная накладная: Накладная001'))

        # Заполнение таблицы Перемещения грузов
        CargoMovement.objects.create(
            cargo=cargo,
            from_transport_bill=transport_bill,
            to_transport_bill=transport_bill,
            transfer_place="Пункт перемещения",
            transfer_date=timezone.now()
        )
        self.stdout.write(self.style.SUCCESS('Добавлено перемещение груза: Наш груз'))
