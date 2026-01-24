# File: cargo_acc/models.py
from django.conf import settings
from django.db import models


# === КОМПАНИИ ===
class Company(models.Model):
    name = models.CharField(max_length=255, unique=True)
    registration = models.CharField(max_length=50)
    tax_id = models.CharField(max_length=50, verbose_name="ИНН/Tax ID")
    ogrn = models.CharField(max_length=50, verbose_name="ОГРН/Registration №")
    legal_address = models.CharField(max_length=500, verbose_name="Юридический адрес")
    actual_address = models.CharField(max_length=500, verbose_name="Фактический адрес", blank=True, null=True)
    representative_fullname = models.CharField(max_length=255, verbose_name="Ф.И.О. представителя")
    representative_basis = models.CharField(max_length=255, verbose_name="Действует на основании")
    phone = models.CharField(max_length=50, verbose_name="Телефон", blank=True, null=True)
    email = models.EmailField(verbose_name="Электронная почта", blank=True, null=True)
    description = models.CharField(max_length=500, blank=True, null=True)

    # === Новые поля для кодогенерации ===
    # Важно: client_counter должен обновляться атомарно (см. cargo_acc/services/code_generator.py),
    # где Company берётся через select_for_update() в транзакции.
    prefix = models.CharField(max_length=2, unique=True, verbose_name="Префикс компании")
    client_counter = models.PositiveIntegerField(default=0)

    # === ФИО директора для договоров ===
    director_fullname = models.CharField(
        max_length=255,
        verbose_name="Ф.И.О. директора",
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Компания"
        verbose_name_plural = "Компании"

    def __str__(self):
        return self.name

# === КЛИЕНТЫ ===
class Client(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="clients")
    client_code = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=500, blank=True, null=True)
    product_counter = models.PositiveIntegerField(default=0)
    cargo_counter = models.PositiveIntegerField(default=0)

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
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="warehouses")
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        verbose_name = "Склад"
        verbose_name_plural = "Склады"
        unique_together = ("company", "name")

    def __str__(self):
        return self.name


# === СПРАВОЧНИКИ ===
class CargoType(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="cargo_types")
    name = models.CharField(max_length=20)
    description = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = "Тип груза"
        verbose_name_plural = "Типы грузов"
        unique_together = ("company", "name")

    def __str__(self):
        return self.name


class CargoStatus(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="cargo_statuses")
    name = models.CharField(max_length=20)
    description = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = "Статус груза"
        verbose_name_plural = "Статусы грузов"
        unique_together = ("company", "name")

    def __str__(self):
        return self.name


# === Тип Упаковки ===
class PackagingType(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="packaging_types")
    name = models.CharField(max_length=20)
    description = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = "Тип упаковки"
        verbose_name_plural = "Типы упаковки"
        unique_together = ("company", "name")

    def __str__(self):
        return self.name


# === Тип начисления ===
class AccrualType(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="accrual_types")
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True, null=True)
    default_amount = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)

    class Meta:
        verbose_name = "Вид начисления"
        verbose_name_plural = "Виды начислений"
        unique_together = ("company", "name")

    def __str__(self):
        return self.name


# === Тип Оплаты ===
class PaymentType(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="payment_types")
    name = models.CharField(max_length=100, unique=False)
    description = models.TextField(blank=True, null=True)

    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Тип оплаты"
        verbose_name_plural = "Типы оплаты"
        indexes = [
            models.Index(fields=["company", "active"]),
        ]

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


# === ГРУЗ (агрегатор) ===
class Cargo(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="cargos")
    client = models.ForeignKey(
        "cargo_acc.Client",
        on_delete=models.PROTECT,
        related_name="cargos",
        db_index=True,
    )
    cargo_code = models.CharField(max_length=50, unique=True, db_index=True)

    # агрегатные параметры (кеш по товарам; пересчитывается сервисом)
    weight_total = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    volume_total = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    # упаковка ГРУЗА (не товара)
    packaging_type = models.ForeignKey(PackagingType, on_delete=models.CASCADE)

    # статус / местоположение (меняются всегда, даже после фиксации состава)
    cargo_status = models.ForeignKey(CargoStatus, on_delete=models.CASCADE, db_index=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)

    # фиксируем только СОСТАВ (add/remove товаров)
    is_locked = models.BooleanField(default=False, db_index=True)
    locked_at = models.DateTimeField(null=True, blank=True)
    locked_by = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="locked_cargos",
    )

    # правило распределения грузовых “добавок” по товарам (на будущее)
    allocation_mode = models.CharField(
        max_length=20,
        choices=[
            ("weight", "По весу"),
            ("volume", "По объёму"),
            ("items", "Поровну по товарам"),
            ("value", "По стоимости товара"),
        ],
        default="weight",
    )

    # QR
    qr_code = models.CharField(max_length=100, blank=True, null=True)

    # служебные поля
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="created_cargos",
    )
    updated_by = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="updated_cargos",
    )

    class Meta:
        verbose_name = "Груз"
        verbose_name_plural = "Грузы"
        indexes = [
            models.Index(fields=["company", "cargo_code"]),
            models.Index(fields=["company", "cargo_status"]),
            models.Index(fields=["company", "warehouse"]),
            models.Index(fields=["company", "created_at"]),
            models.Index(fields=["company", "is_locked"]),
        ]

    def __str__(self):
        return self.cargo_code


# === ТОВАРЫ (первоисточник) ===
class Product(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="client_products")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="products")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    cargo = models.ForeignKey(Cargo, on_delete=models.SET_NULL, null=True, blank=True)
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


# === ДОПОЛНИТЕЛЬНЫЕ ЗАТРАТЫ ===
class ExtraCost(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="extra_costs")
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


# ================
# === ПЛАТЕЖИ ====
# ================
# === Оплаты и Начисления клиентов ===
class Payment(models.Model):
    company = models.ForeignKey("Company", on_delete=models.CASCADE, related_name="payments")
    client = models.ForeignKey("Client", on_delete=models.CASCADE, related_name="client_payments")
    payment_date = models.DateField()
    operation_kind = models.IntegerField(
        choices=[(1, "Оплата"), (2, "Начисление")],
        null=False
    )
    payment_type = models.ForeignKey(  # ← справочник видов оплат
        "PaymentType",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="payment_operations"
    )
    accrual_type = models.ForeignKey(  # ← справочник видов начислений
        "AccrualType",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="accrual_operations"
    )

    # Списки товаров/грузов
    products = models.JSONField(default=list, blank=True)
    cargos = models.JSONField(default=list, blank=True)

    # Суммы
    amount_total = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=10, default="RUB")
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, default=1.0000)
    amount_usd = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    # Метод оплаты
    method = models.CharField(
        max_length=20,
        choices=[
            ("cash", "Наличные"),
            ("bank", "Безнал"),
            ("pos", "POS-терминал"),
            ("offset", "Взаимозачёт"),
        ],
        default="bank",
    )

    # Комментарий
    comment = models.TextField(blank=True, null=True)

    # Служебное
    is_locked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_payments",
    )

    class Meta:
        verbose_name = "Операция"
        verbose_name_plural = "Операции"
        indexes = [
            models.Index(fields=["company", "client"]),
            models.Index(fields=["payment_date"]),
        ]

    def save(self, *args, **kwargs):
        if self.currency == "USD":
            self.exchange_rate = 1
            self.amount_usd = self.amount_total
        else:
            try:
                self.amount_usd = round(float(self.amount_total) / float(self.exchange_rate), 2)
            except Exception:
                self.amount_usd = 0
        super().save(*args, **kwargs)


# === Снапшот - срез взаиморасчетов на конец месяца ===
class Snapshot(models.Model):
    company = models.ForeignKey(
        "Company", on_delete=models.CASCADE, related_name="snapshots"
    )
    client = models.ForeignKey(
        "Client", on_delete=models.CASCADE, related_name="client_snapshots"
    )

    snapshot_date = models.DateTimeField()

    balance_total = models.DecimalField(max_digits=14, decimal_places=2)
    details_json = models.JSONField(default=dict)

    hash_before = models.CharField(max_length=64)
    dirty_flag = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    recalculated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Срез баланса"
        verbose_name_plural = "Срезы баланса"
        indexes = [
            models.Index(fields=["company", "client"]),
            models.Index(fields=["snapshot_date"]),
            models.Index(fields=["dirty_flag"]),
        ]

    def __str__(self):
        return f"Snapshot {self.client} — {self.snapshot_date}"


# === ПЕРЕВОЗКА, ТРАНСПОРТ, СТАТУСЫ ===
class CarrierCompany(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="carrier_companies")
    is_shared = models.BooleanField(default=False)
    name = models.CharField(max_length=255)
    registration = models.CharField(max_length=50)
    description = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        verbose_name = "Перевозчик"
        verbose_name_plural = "Перевозчики"

    def __str__(self):
        return self.name


# === Транспорт перевозки ===
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


# === Транспортная накладная ===
class TransportBill(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="transport_bills")
    bill_code = models.CharField(max_length=20, unique=True)
    cargos = models.ManyToManyField(Cargo, related_name="cargos_bills")
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    carrier_company = models.ForeignKey(CarrierCompany, on_delete=models.CASCADE)
    departure_place = models.CharField(max_length=200, blank=True, null=True)
    destination_place = models.CharField(max_length=200, blank=True, null=True)
    departure_date = models.DateField()
    arrival_date = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Транспортная накладная"
        verbose_name_plural = "Транспортные накладные"

    def __str__(self):
        return self.bill_code


# === Перемещение груза
class CargoMovement(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="cargo_movements")
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


# === История действий в системе ===
class SystemActionLog(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    # что изменили
    model_name = models.CharField(max_length=100)
    object_id = models.IntegerField()
    action = models.CharField(max_length=20)

    # данные
    diff = models.JSONField(null=True, blank=True)
    old_data = models.JSONField(null=True, blank=True)
    new_data = models.JSONField(null=True, blank=True)

    # кто
    operator = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    ip = models.GenericIPAddressField(null=True, blank=True)

    # когда (единственное поле)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Системный лог"
        verbose_name_plural = "Системные логи"

    def __str__(self):
        return f"{self.model_name} #{self.object_id} — {self.action}"


# === КУРСЫ ВАЛЮТ ===
class CurrencyRate(models.Model):
    date = models.DateField()
    currency = models.CharField(max_length=10)
    rate = models.DecimalField(max_digits=14, decimal_places=6, help_text="Курс валюты к USD")
    custom_rate = models.DecimalField(max_digits=14, decimal_places=6, null=True, blank=True,
                                      help_text="Переопределённый (наш) курс")
    conversion_percent = models.DecimalField(max_digits=6, decimal_places=2, default=0,
                                             help_text="Коррекция в % относительно официального курса")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Курс валют"
        verbose_name_plural = "Курсы валют"
        unique_together = ("date", "currency")
        indexes = [
            models.Index(fields=["currency"]),
            models.Index(fields=["date"]),
        ]

    def __str__(self):
        return f"{self.date} — {self.currency} = {self.rate}"


# === Тариф Доставки ===
class Tariff(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="tariffs")
    name = models.CharField(max_length=50)

    # Тариф для определённого типа товара
    cargo_type = models.ForeignKey(CargoType, on_delete=models.CASCADE)

    # weight / volume / density
    calc_mode = models.CharField(
        max_length=20,
        choices=[
            ("weight", "По весу"),
            ("volume", "По объёму"),
            ("density", "По плотности"),
        ]
    )

    base_rate = models.DecimalField(max_digits=14, decimal_places=4)  # ставка за кг/куб
    packaging_rate = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    insurance_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    minimal_cost = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = "Тариф"
        verbose_name_plural = "Тарифы"
        unique_together = ("company", "name")

    def __str__(self):
        return self.name
