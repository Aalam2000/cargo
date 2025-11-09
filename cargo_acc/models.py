# File: cargo_acc/models.py
from django.conf import settings
from django.db import models


# === КОМПАНИИ ===
class Company(models.Model):
    name = models.CharField(max_length=255, unique=True)
    registration = models.CharField(max_length=50)
    description = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        verbose_name = "Компания"
        verbose_name_plural = "Компании"

    def __str__(self):
        return self.name


# === КЛИЕНТЫ ===
class Client(models.Model):
    client_code = models.CharField(max_length=20, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    description = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"

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


# === СКЛАДЫ ===
class Warehouse(models.Model):
    name = models.CharField(max_length=100, unique=True)
    address = models.CharField(max_length=500, blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Склад"
        verbose_name_plural = "Склады"

    def __str__(self):
        return self.name


# === СПРАВОЧНИКИ ===
class CargoType(models.Model):
    name = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = "Тип груза"
        verbose_name_plural = "Типы грузов"

    def __str__(self):
        return self.name


class CargoStatus(models.Model):
    name = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = "Статус груза"
        verbose_name_plural = "Статусы грузов"

    def __str__(self):
        return self.name


class PackagingType(models.Model):
    name = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = "Тип упаковки"
        verbose_name_plural = "Типы упаковки"

    def __str__(self):
        return self.name


# === ИЗОБРАЖЕНИЯ и QR ===
class Image(models.Model):
    image_file = models.ImageField(upload_to='img/', default='img/default_image.jpg')
    upload_date = models.DateTimeField(auto_now_add=True)
    operator = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    geo_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    geo_lon = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    object_type = models.CharField(max_length=50, blank=True, null=True)
    object_id = models.PositiveBigIntegerField(null=True, blank=True)
    description = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = "Изображение"
        verbose_name_plural = "Изображения"

    def __str__(self):
        return f"{self.image_file.name} ({self.object_type or 'unlinked'})"


class QRScan(models.Model):
    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='qr_scans')
    decoded_data = models.CharField(max_length=255, blank=True, null=True)
    recognized_type = models.CharField(max_length=50, blank=True, null=True)
    recognized_id = models.PositiveBigIntegerField(null=True, blank=True)
    recognized_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[('success', 'Success'), ('fail', 'Fail'), ('uncertain', 'Uncertain')],
        default='uncertain'
    )
    action_result = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = "Скан QR-кода"
        verbose_name_plural = "Сканирование QR-кодов"

    def __str__(self):
        return f"QRScan {self.id} ({self.status})"


# === ТОВАРЫ (первоисточник) ===
class Product(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    product_code = models.CharField(max_length=30, unique=True)
    cargo_type = models.ForeignKey(CargoType, on_delete=models.CASCADE)
    cargo_status = models.ForeignKey(CargoStatus, on_delete=models.CASCADE)
    packaging_type = models.ForeignKey(PackagingType, on_delete=models.CASCADE)
    qr_code = models.CharField(max_length=100, unique=True, blank=True, null=True)
    qr_created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    record_date = models.DateField(null=True, blank=True)
    cargo_description = models.CharField(max_length=500, blank=True, null=True)
    departure_place = models.CharField(max_length=200, blank=True, null=True)
    destination_place = models.CharField(max_length=200, blank=True, null=True)
    weight = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    volume = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    cost = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    insurance = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    delivery_time = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    shipping_date = models.DateField(null=True, blank=True)
    delivery_date = models.DateField(null=True, blank=True)
    comment = models.CharField(max_length=500, blank=True, null=True)
    images = models.ManyToManyField(Image, blank=True)

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __str__(self):
        return self.product_code


# === ГРУЗ (агрегатор) ===
class Cargo(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    cargo_code = models.CharField(max_length=50, unique=True)
    products = models.ManyToManyField(Product, blank=True)
    departure_place = models.CharField(max_length=200, blank=True, null=True)
    destination_place = models.CharField(max_length=200, blank=True, null=True)
    weight_total = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    volume_total = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    shipping_date = models.DateField(null=True, blank=True)
    delivery_date = models.DateField(null=True, blank=True)
    cargo_status = models.ForeignKey(CargoStatus, on_delete=models.CASCADE)
    packaging_type = models.ForeignKey(PackagingType, on_delete=models.CASCADE)
    last_status = models.ForeignKey(CargoStatus, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='current_cargos')

    class Meta:
        verbose_name = "Груз"
        verbose_name_plural = "Грузы"

    def __str__(self):
        return self.cargo_code


# === ДОПОЛНИТЕЛЬНЫЕ ЗАТРАТЫ ===
class ExtraCost(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True)
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    cost_type = models.CharField(
        max_length=50,
        choices=[
            ('loading', 'Погрузка'),
            ('unloading', 'Разгрузка'),
            ('packing', 'Упаковка'),
            ('storage', 'Хранение'),
            ('customs', 'Таможня'),
            ('transport', 'Транспортировка'),
            ('other', 'Прочее'),
        ],
        default='other'
    )
    description = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    allocated = models.BooleanField(default=False)
    is_for_cargo = models.BooleanField(default=False,
                                       help_text="True — если расход относится ко всему грузу, False — если к товару")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='created_extracosts'
    )

    class Meta:
        verbose_name = "Дополнительная затрата"
        verbose_name_plural = "Дополнительные затраты"

    def __str__(self):
        target = self.product or self.cargo
        return f"{self.cost_type} — {self.amount} ({target})"


class ExtraCostAllocation(models.Model):
    extra_cost = models.ForeignKey(ExtraCost, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        verbose_name = "Распределение затрат"
        verbose_name_plural = "Распределения затрат"

    def __str__(self):
        return f"{self.extra_cost.cost_type} → {self.product.product_code} ({self.amount})"


# === ПЛАТЕЖИ ===
class Payment(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='payments')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateField()
    amount_total = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=10, default='RUB')
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, default=1.0000)
    amount_usd = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    method = models.CharField(
        max_length=20,
        choices=[
            ('cash', 'Наличные'),
            ('bank', 'Безнал'),
            ('pos', 'POS-терминал'),
            ('offset', 'Взаимозачёт'),
        ],
        default='bank'
    )
    comment = models.TextField(blank=True, null=True)
    is_locked = models.BooleanField(default=False)
    payment_type = models.CharField(
        max_length=20,
        choices=[
            ('accrual', 'Начисление'),
            ('payment', 'Оплата'),
        ],
        default='payment'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='created_payments'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Оплата"
        verbose_name_plural = "Оплаты"
        indexes = [
            models.Index(fields=["company", "client"]),
            models.Index(fields=["payment_date"]),
        ]

    def __str__(self):
        return f"{self.client} — {self.amount_total} {self.currency} ({self.payment_type})"

    def save(self, *args, **kwargs):
        if self.currency == "USD":
            self.exchange_rate = 1
            self.amount_usd = self.amount_total
        elif not self.amount_usd:
            try:
                self.amount_usd = round(float(self.amount_total) / float(self.exchange_rate), 2)
            except Exception:
                self.amount_usd = 0
        super().save(*args, **kwargs)



class PaymentProduct(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='allocations')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='payment_links')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='payment_product_allocations')
    allocated_amount = models.DecimalField(max_digits=14, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Оплата по товару"
        verbose_name_plural = "Оплаты по товарам"
        unique_together = ('payment', 'product')
        indexes = [
            models.Index(fields=["company"]),
            models.Index(fields=["product"]),
        ]

    def __str__(self):
        return f"{self.product} — {self.allocated_amount}"


# === ПЕРЕВОЗКА, ТРАНСПОРТ, СТАТУСЫ ===
class CarrierCompany(models.Model):
    name = models.CharField(max_length=255, unique=True)
    registration = models.CharField(max_length=50)
    description = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        verbose_name = "Перевозчик"
        verbose_name_plural = "Перевозчики"

    def __str__(self):
        return self.name


class Vehicle(models.Model):
    license_plate = models.CharField(max_length=20, unique=True)
    model = models.CharField(max_length=100, blank=True, null=True)
    carrier_company = models.ForeignKey(CarrierCompany, on_delete=models.CASCADE)
    current_status = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = "Транспорт"
        verbose_name_plural = "Транспорт"

    def __str__(self):
        return self.license_plate


class TransportBill(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    bill_code = models.CharField(max_length=20, unique=True)
    cargos = models.ManyToManyField(Cargo)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    departure_place = models.CharField(max_length=200, blank=True, null=True)
    destination_place = models.CharField(max_length=200, blank=True, null=True)
    departure_date = models.DateField()
    arrival_date = models.DateField(null=True, blank=True)
    carrier_company = models.ForeignKey(CarrierCompany, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Транспортная накладная"
        verbose_name_plural = "Транспортные накладные"

    def __str__(self):
        return self.bill_code


class CargoMovement(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE)
    from_transport_bill = models.ForeignKey(TransportBill, related_name='from_transport_bill', on_delete=models.CASCADE)
    to_transport_bill = models.ForeignKey(TransportBill, related_name='to_transport_bill', on_delete=models.CASCADE)
    transfer_place = models.CharField(max_length=255, blank=True, null=True)
    transfer_date = models.DateTimeField()
    status_before = models.ForeignKey(CargoStatus, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='status_before_moves')
    status_after = models.ForeignKey(CargoStatus, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='status_after_moves')
    image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True, blank=True)
    qrscan = models.ForeignKey(QRScan, on_delete=models.SET_NULL, null=True, blank=True)
    operator = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    recognized_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Перемещение груза"
        verbose_name_plural = "Перемещения грузов"

    def __str__(self):
        return f'Move {self.cargo} from {self.from_transport_bill} to {self.to_transport_bill}'


class CargoStatusLog(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE, related_name='status_logs')
    status = models.ForeignKey(CargoStatus, on_delete=models.CASCADE)
    changed_at = models.DateTimeField(auto_now_add=True)
    image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True, blank=True)
    qrscan = models.ForeignKey(QRScan, on_delete=models.SET_NULL, null=True, blank=True)
    operator = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    comment = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = "История статуса"
        verbose_name_plural = "История статусов"

    def __str__(self):
        return f"{self.cargo.cargo_code} → {self.status.name} ({self.changed_at.strftime('%Y-%m-%d %H:%M')})"
