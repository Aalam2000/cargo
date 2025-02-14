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

class Image(models.Model):
    image_file = models.ImageField(upload_to='img/', default='img/default_image.jpg')
    upload_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.image_file.name

# Модель Товаров
class Product(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    product_code = models.CharField(max_length=30, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
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
    cargo_code = models.CharField(max_length=20, unique=True)
    products = models.ManyToManyField(Product)
    images = models.ManyToManyField(Image)
    departure_place = models.CharField(max_length=200, blank=True, null=True)
    destination_place = models.CharField(max_length=200, blank=True, null=True)
    weight = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)  # Изменено
    volume = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)  # Изменено
    cost = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)  # Изменено
    insurance = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)  # Изменено
    dimensions = models.CharField(max_length=30, blank=True, null=True)
    shipping_date = models.DateField(null=True, blank=True)
    delivery_date = models.DateField(null=True, blank=True)
    cargo_status = models.ForeignKey(CargoStatus, on_delete=models.CASCADE)
    packaging_type = models.ForeignKey(PackagingType, on_delete=models.CASCADE)
    delivery_time = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Изменено

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

    def __str__(self):
        return f'Move {self.cargo} from {self.from_transport_bill} to {self.to_transport_bill}'
