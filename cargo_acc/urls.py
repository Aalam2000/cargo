# cargo_acc/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from cargodb import views as core_views
from . import views, views_payment, views_table
from .views_invoice import product_invoice_pdf

# --------------------------------------------------------------------
# 📦 ROUTER — стандартные ViewSet API (CRUD для моделей)
# --------------------------------------------------------------------
router = DefaultRouter()
router.register(r'companies', views_table.CompanyViewSet, basename='company')
router.register(r'clients', views_table.ClientViewSet, basename='client')
router.register(r'warehouses', views_table.WarehouseViewSet, basename='warehouse')
router.register(r'cargo-types', views_table.CargoTypeViewSet, basename='cargotype')
router.register(r'cargo-statuses', views_table.CargoStatusViewSet, basename='cargostatus')
router.register(r'packaging-types', views_table.PackagingTypeViewSet, basename='packagingtype')
router.register(r'accrual-types', views_table.AccrualTypeViewSet, basename='accrualtype')
router.register(r'images', views_table.ImageViewSet, basename='image')
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'cargos', views.CargoViewSet, basename='cargo')
router.register(r'carrier-companies', views.CarrierCompanyViewSet, basename='carriercompany')
router.register(r'vehicles', views.VehicleViewSet, basename='vehicle')
router.register(r'transport-bills', views.TransportBillViewSet, basename='transportbill')
router.register(r'cargo-movements', views.CargoMovementViewSet, basename='cargomovement')
router.register(r'payment-types', views_table.PaymentTypeViewSet, basename='paymenttype')
router.register(r'products-table', views_table.ProductsTableViewSet, basename='products-table')
router.register(r'tariffs', views_table.TariffViewSet, basename='tariff')
router.register(r'currency-rates', views_table.CurrencyRateViewSet, basename='currencyrate')


# --------------------------------------------------------------------
# 🌐 URLPATTERNS — основные маршруты приложения cargo_acc
# --------------------------------------------------------------------
urlpatterns = [

    # --- Базовый API роутер ---
    path('api/', include(router.urls)),

    # --------------------------------------------------------------
    # ⚙️ Настройки таблиц (универсальные)
    # --------------------------------------------------------------
    path('api/get_table_settings/', views.get_table_settings, name='get_table_settings'),
    path('api/save_table_settings/', views.save_table_settings, name='save_table_settings'),

    # --------------------------------------------------------------
    # 🧾 Клиентская таблица (для отображения грузов)
    # --------------------------------------------------------------
    path('client_table/', views.client_table_page, name='client_table_page'),
    path('client_table/data/', views.client_table_data, name='client_table_data'),

    # --------------------------------------------------------------
    # 🔍 Проверка уникальности и валидации полей
    # --------------------------------------------------------------
    path('api/check_client_code/', views.check_client_code, name='check_client_code'),
    path('api/check_company_name/', views.check_company_name, name='check_company_name'),
    path('api/check_warehouse_name/', views.check_warehouse_name, name='check_warehouse_name'),
    path('api/check_cargo_type_name/', views.check_cargo_type_name, name='check_cargo_type_name'),
    path('api/check_cargo_status_name/', views.check_cargo_status_name, name='check_cargo_status_name'),
    path('api/check_packaging_type_name/', views.check_packaging_type_name, name='check_packaging_type_name'),

    # --------------------------------------------------------------
    # 🧠 Получение справочников (для фильтров, форм и селектов)
    # --------------------------------------------------------------
    path('api/get_clients/', views.get_clients, name='get_clients'),
    path("api/table/<str:model_name>/", views_table.get_table, name="get_table"),
    path('api/get_companies/', views.get_companies, name='get_companies'),

    # --------------------------------------------------------------
    # 🧾 Работа с продуктами и изображениями
    # --------------------------------------------------------------
    path('products/<int:product_id>/add-image/', views.add_image_to_product, name='add_image_to_product'),

    # --- Интерфейсы оператора ---
    path('operator/clients_payments/', views.operator_clients, name='operator_clients'),

    # --------------------------------------------------------------
    # ⚡ SSE (реальное время, стриминг)
    # --------------------------------------------------------------
    path('clients/stream/', views.sse_clients_stream, name='clients_stream'),

    # --------------------------------------------------------------
    # 🧰 Универсальные операции добавления/удаления строк
    # --------------------------------------------------------------
    path('mod_addrow/', views.mod_addrow_view, name='mod_addrow'),
    path('mod_delrow/', views.mod_delrow_view, name='mod_delrow'),
    path('api/delete/<str:model_name>/<int:pk>/', views.UniversalDeleteView.as_view(), name='universal_delete'),

    # --------------------------------------------------------------
    # ⚙️ Модалки и настройки интерфейса
    # --------------------------------------------------------------
    path('settings_modal', views.settings_modal, name='settings_modal'),

    # === Оплаты клиентов ===
    path("api/add_payment/", views_payment.add_or_edit_payment, name="add_payment"),

    # === Таблицы и API-грузов ===
    path("api/cargo_table/data/", core_views.cargo_table_data, name="cargo_table_data"),
    path("api/cargo_table/config/", core_views.cargo_table_config, name="cargo_table_config"),
    path("api/table_data/", core_views.api_table_data, name="api_table_data"),

    # === Служебные и API-запросы ===
    path("api/log/", core_views.js_log, name="js_log"),  # логирование ошибок JS
    # === Курс валют (Google Finance proxy) ===
    path("api/get_rate/", views_payment.get_currency_rate, name="get_currency_rate"),
    # в cargo_acc/urls.py (рядом с client_table/ и другими страницами)
    path('references/', views.references_page, name='references_page'),
    # в cargo_acc/urls.py: добавить в urlpatterns
    path('products/', views.products_page, name='products_page'),
    path("api/company/<int:pk>/", views_table.get_company, name="get_company"),
    path("api/company/<int:pk>/update/", views_table.update_company, name="update_company"),
    path("api/products_table/", views_table.products_table_view, name="products_table"),
    path("api/client_balance/", views_payment.client_balance, name="client_balance"),
    path("api/payments_table/", views_payment.payments_table, name="payments_table"),
    path("api/product/<int:pk>/invoice/", product_invoice_pdf, name="product_invoice"),
    path("api/generate/client/", views_table.api_generate_client_code),
    path("api/generate/product/", views_table.api_generate_product_code),
    path("api/generate/cargo/", views_table.api_generate_cargo_code),
]
