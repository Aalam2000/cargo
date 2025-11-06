# cargo_acc/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# --------------------------------------------------------------------
# 📦 ROUTER — стандартные ViewSet API (CRUD для моделей)
# --------------------------------------------------------------------
router = DefaultRouter()
router.register(r'companies', views.CompanyViewSet)
router.register(r'clients', views.ClientViewSet)
router.register(r'warehouses', views.WarehouseViewSet)
router.register(r'cargo-types', views.CargoTypeViewSet)
router.register(r'cargo-statuses', views.CargoStatusViewSet)
router.register(r'packaging-types', views.PackagingTypeViewSet)
router.register(r'images', views.ImageViewSet)
router.register(r'products', views.ProductViewSet)
router.register(r'cargos', views.CargoViewSet)
router.register(r'carrier-companies', views.CarrierCompanyViewSet)
router.register(r'vehicles', views.VehicleViewSet)
router.register(r'transport-bills', views.TransportBillViewSet)
router.register(r'cargo-movements', views.CargoMovementViewSet)

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
    path('api/get_warehouses/', views.get_warehouses, name='get_warehouses'),
    path('api/get_companies/', views.get_companies, name='get_companies'),
    path('api/get_cargo_types/', views.get_cargo_types, name='get_cargo_types'),
    path('api/get_cargo_statuses/', views.get_cargo_statuses, name='get_cargo_statuses'),
    path('api/get_packaging_types/', views.get_packaging_types, name='get_packaging_types'),

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

    # === Раздел заказов ===

    # === Подключение модулей ===
    path('cargo_acc/', include('cargo_acc.urls')),  # все маршруты приложения cargo_acc
    path('chatgpt_ui/', include('chatgpt_ui.urls')),  # внутренний модуль ChatGPT UI

    # === Таблицы и API-грузов ===
    path("api/cargo_table/data/", views.cargo_table_data, name="cargo_table_data"),  # JSON-данные таблицы
    path("api/cargo_table/config/", views.cargo_table_config, name="cargo_table_config"),
    path("api/table_data/", views.api_table_data, name="api_table_data"),

    # === Служебные и API-запросы ===
    path("api/log/", views.js_log, name="js_log"),  # логирование ошибок JS

]
