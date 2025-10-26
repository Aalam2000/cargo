# File: cargo_acc/models.py

from django.db import models


# Модель Компании
class Company(models.Model):
    name = models.CharField(max_length=255, unique=True)
    registration = models.CharField(max_length=50)
    description = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.name


# Модель Клиента
class Client(models.Model):
    client_code = models.CharField(max_length=20, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    description = models.CharField(max_length=500, blank=True, null=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        from .views import mark_clients_changed
        mark_clients_changed()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        from .views import mark_clients_changed
        mark_clients_changed()

    def __str__(self):
        return self.client_code


# Модель Склада
class Warehouse(models.Model):
    name = models.CharField(max_length=100, unique=True)
    address = models.CharField(max_length=500, blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


# Модель Типов груза
class CargoType(models.Model):
    name = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name


# Модель Статуса груза
class CargoStatus(models.Model):
    name = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name


# Модель Типов упаковок
class PackagingType(models.Model):
    name = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name


# Модель Фоток
class Image(models.Model):
    image_file = models.ImageField(upload_to='img/', default='img/default_image.jpg')
    upload_date = models.DateTimeField(auto_now_add=True)

    # 🔹 Новые поля для фотофиксации
    operator = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    geo_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    geo_lon = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    object_type = models.CharField(max_length=50, blank=True, null=True)  # cargo / product / transportbill / etc.
    object_id = models.PositiveBigIntegerField(null=True, blank=True)  # ссылка на объект (без FK)
    description = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.image_file.name} ({self.object_type or 'unlinked'})"


# Модель распознавания QR-кодов
class QRScan(models.Model):
    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='qr_scans')
    decoded_data = models.CharField(max_length=255, blank=True, null=True)
    recognized_type = models.CharField(max_length=50, blank=True, null=True)  # cargo / product / transportbill
    recognized_id = models.PositiveBigIntegerField(null=True, blank=True)  # id объекта
    recognized_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[('success', 'Success'), ('fail', 'Fail'), ('uncertain', 'Uncertain')],
        default='uncertain'
    )
    action_result = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"QRScan {self.id} ({self.status})"


# Модель Товаров
class Product(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    product_code = models.CharField(max_length=30, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    qr_code = models.CharField(max_length=100, unique=True, blank=True, null=True)
    qr_created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    record_date = models.DateField(null=True, blank=True)
    cargo_description = models.CharField(max_length=500, blank=True, null=True)
    cargo_type = models.ForeignKey(CargoType, on_delete=models.CASCADE)
    departure_place = models.CharField(max_length=200, blank=True, null=True)
    destination_place = models.CharField(max_length=200, blank=True, null=True)
    weight = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    volume = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    cost = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    insurance = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    dimensions = models.CharField(max_length=30, blank=True, null=True)
    shipping_date = models.DateField(null=True, blank=True)
    delivery_date = models.DateField(null=True, blank=True)
    cargo_status = models.ForeignKey(CargoStatus, on_delete=models.CASCADE)
    images = models.ManyToManyField(Image)
    packaging_type = models.ForeignKey(PackagingType, on_delete=models.CASCADE)
    delivery_time = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    comment = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.product_code


# Модель Грузов
class Cargo(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    cargo_code = models.CharField(max_length=50, unique=True)
    products = models.ManyToManyField(Product)
    images = models.ManyToManyField(Image)
    qr_code = models.CharField(max_length=100, unique=True, blank=True, null=True)
    qr_created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    # Локации
    departure_place = models.CharField(max_length=200, blank=True, null=True)
    destination_place = models.CharField(max_length=200, blank=True, null=True)

    # Количественные показатели
    places_count = models.IntegerField(null=True, blank=True)  # КОЛ. МЕСТ
    weight = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    volume = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    # Тарифы/стоимости по доставке
    cost = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)           # Итог по доставке
    insurance = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)      # Страховка
    packaging_cost = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True) # СТ.УПАК
    tariff_weight = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)  # тариф (по весу)
    tariff_min = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)     # тариф от ...

    # Прочее
    cargo_description = models.CharField(max_length=500, blank=True, null=True)  # текст из CSV (временное поле)
    dimensions = models.CharField(max_length=30, blank=True, null=True)

    # Даты и статус
    shipping_date = models.DateField(null=True, blank=True)
    delivery_date = models.DateField(null=True, blank=True)
    delivery_time = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # число дней
    cargo_status = models.ForeignKey(CargoStatus, on_delete=models.CASCADE)
    packaging_type = models.ForeignKey(PackagingType, on_delete=models.CASCADE)

    def __str__(self):
        return self.cargo_code



# Модель Компаний-перевозчиков
class CarrierCompany(models.Model):
    name = models.CharField(max_length=255, unique=True)
    registration = models.CharField(max_length=50)
    description = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.name


# Модель Автомобилей
class Vehicle(models.Model):
    license_plate = models.CharField(max_length=20, unique=True)
    model = models.CharField(max_length=100, blank=True, null=True)
    carrier_company = models.ForeignKey(CarrierCompany, on_delete=models.CASCADE)
    current_status = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.license_plate


# Модель Транспортных накладных
class TransportBill(models.Model):
    bill_code = models.CharField(max_length=20, unique=True)
    cargos = models.ManyToManyField(Cargo)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    departure_place = models.CharField(max_length=200, blank=True, null=True)
    destination_place = models.CharField(max_length=200, blank=True, null=True)
    departure_date = models.DateField()
    arrival_date = models.DateField(null=True, blank=True)
    carrier_company = models.ForeignKey(CarrierCompany, on_delete=models.CASCADE)

    def __str__(self):
        return self.bill_code


# Модель Перемещения грузов
class CargoMovement(models.Model):
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE)
    from_transport_bill = models.ForeignKey(TransportBill, related_name='from_transport_bill', on_delete=models.CASCADE)
    to_transport_bill = models.ForeignKey(TransportBill, related_name='to_transport_bill', on_delete=models.CASCADE)
    transfer_place = models.CharField(max_length=255, blank=True, null=True)
    transfer_date = models.DateTimeField()
    image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True, blank=True)
    qrscan = models.ForeignKey('QRScan', on_delete=models.SET_NULL, null=True, blank=True)
    operator = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    recognized_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'Move {self.cargo} from {self.from_transport_bill} to {self.to_transport_bill}'


# Модель истории изменения статусов груза
class CargoStatusLog(models.Model):
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE, related_name='status_logs')
    status = models.ForeignKey(CargoStatus, on_delete=models.CASCADE)
    changed_at = models.DateTimeField(auto_now_add=True)
    image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True, blank=True)
    qrscan = models.ForeignKey('QRScan', on_delete=models.SET_NULL, null=True, blank=True)
    operator = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    comment = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.cargo.cargo_code} → {self.status.name} ({self.changed_at.strftime('%Y-%m-%d %H:%M')})"

# --- ПЛАТЕЖИ ---

class Payment(models.Model):
    """
    Финансовый платёж от клиента. Заполняется:
    - при импорте старых данных (payment_source='import_csv'),
    - вручную оператором,
    - автоматически из вебхука банка/СБП (с qr_payload/reference_number).
    """
    payment_code = models.CharField(max_length=50, unique=True)  # внутренний код платежа
    payment_date = models.DateField()                             # дата поступления денег

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    # Суммы и валюта
    currency = models.CharField(max_length=10, default='USD')
    amount_original = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    amount_usd = models.DecimalField(max_digits=15, decimal_places=2)

    # Источники и идентификаторы
    payment_method = models.CharField(max_length=50, blank=True, null=True)     # cash/bank/SBP/etc
    payment_source = models.CharField(max_length=50, default='manual')          # manual/import_csv/SBP/bank/web
    reference_number = models.CharField(max_length=100, blank=True, null=True)  # ID транзакции банка/СБП
    qr_payload = models.TextField(blank=True, null=True)                        # содержимое QR (JSON-строка)
    payer_phone = models.CharField(max_length=30, blank=True, null=True)

    # Аудит
    verified_at = models.DateTimeField(blank=True, null=True)
    operator = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['payment_date']),
            models.Index(fields=['client']),
            models.Index(fields=['company']),
        ]
        constraints = [
            # защитимся от дублей банковских транзакций в рамках источника
            models.UniqueConstraint(fields=['reference_number', 'payment_source'],
                                    name='uniq_payment_ref_by_source',
                                    condition=~models.Q(reference_number=None)),
        ]

    def __str__(self):
        return f"{self.payment_code} | {self.client.client_code} | {self.amount_usd} {self.currency}"


class PaymentCargo(models.Model):
    """
    Распределение суммы платежа по грузам (частично или полностью).
    Один платёж может закрывать несколько грузов, и наоборот.
    """
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='cargo_links')
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE, related_name='payment_links')
    amount_usd = models.DecimalField(max_digits=15, decimal_places=2)  # часть суммы, идущая на этот груз
    comment = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = [('payment', 'cargo')]
        indexes = [
            models.Index(fields=['payment']),
            models.Index(fields=['cargo']),
        ]

    def __str__(self):
        return f"{self.payment.payment_code} → {self.cargo.cargo_code}: {self.amount_usd} USD"
