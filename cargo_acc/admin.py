# cargo_acc/admin.py
from django.contrib import admin
from .models import (
    Company,
    Client,
    Warehouse,
    CargoType,
    CargoStatus,
    PackagingType,
    AccrualType,
    PaymentType,
    Image,
    QRScan,
    Product,
    Cargo,
    ExtraCost,
    ExtraCostAllocation,
    Payment,
    Snapshot,
    CarrierCompany,
    Vehicle,
    TransportBill,
    CargoMovement,
    SystemActionLog,
    CurrencyRate,
)

# 🔹 Универсальный класс администратора с ID
class DefaultAdmin(admin.ModelAdmin):
    def get_list_display(self, request):
        """
        Автоматически добавляем поле 'id' + первые несколько полей модели.
        """
        model_fields = [f.name for f in self.model._meta.fields]
        display_fields = ["id"] + [f for f in model_fields if f != "id"][:4]  # первые 4 для наглядности
        return display_fields

    list_display_links = ("id",)
    ordering = ("-id",)

# 🔹 Список всех моделей для регистрации
models_list = [
    Company,
    Client,
    Warehouse,
    CargoType,
    CargoStatus,
    PackagingType,
    AccrualType,
    PaymentType,
    Image,
    QRScan,
    Product,
    Cargo,
    ExtraCost,
    ExtraCostAllocation,
    Payment,
    Snapshot,
    CarrierCompany,
    Vehicle,
    TransportBill,
    CargoMovement,
    SystemActionLog,
    CurrencyRate,
]


# 🔹 Универсальная регистрация с DefaultAdmin
for model in models_list:
    try:
        admin.site.register(model, DefaultAdmin)
    except admin.sites.AlreadyRegistered:
        pass
