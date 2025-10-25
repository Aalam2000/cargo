from django.contrib import admin
from .models import *

# 🔹 Полный список всех моделей для регистрации
models_list = [
    Company,
    Client,
    Warehouse,
    CargoType,
    CargoStatus,
    PackagingType,
    Image,
    Product,
    Cargo,
    CarrierCompany,
    Vehicle,
    TransportBill,
    CargoMovement,
    QRScan,
    CargoStatusLog,
]

# 🔹 Универсальная регистрация без дубликатов
for model in models_list:
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        pass
