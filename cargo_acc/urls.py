from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

'''(
    CompanyViewSet, ClientViewSet, WarehouseViewSet, CargoTypeViewSet, CargoStatusViewSet,
    PackagingTypeViewSet, ImageViewSet, ProductViewSet, CargoViewSet, CarrierCompanyViewSet,
    VehicleViewSet, TransportBillViewSet, CargoMovementViewSet, get_table_settings, save_table_settings,
    check_client_code_unique
)
'''
# Создаем router для автоматической генерации путей
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

# Подключаем router к маршруту API
urlpatterns = [
    path('api/', include(router.urls)),  # Все API маршруты будут начинаться с /api/
    path('api/get_table_settings/', views.get_table_settings, name='get_table_settings'),  # Для получения настроек
    path('api/save_table_settings/', views.save_table_settings, name='save_table_settings'),  # Для сохранения настроек
    path('api/check_client_code/', views.check_client_code, name='check_client_code'),
    path('api/check_company_name/', views.check_company_name, name='check_company_name'),
    path('api/check_warehouse_name/', views.check_warehouse_name, name='check_warehouse_name'),
    path('api/check_cargo_type_name/', views.check_cargo_type_name, name='check_cargo_type_name'),
    path('api/check_cargo_status_name/', views.check_cargo_status_name, name='check_cargo_status_name'),
    path('api/check_packaging_type_name/', views.check_packaging_type_name, name='check_packaging_type_name'),
    path('products/<int:product_id>/add-image/', views.add_image_to_product, name='add_image_to_product'),
    path('client_table/', views.client_table_page, name='client_table_page'),
    path('client_table/data/', views.client_table_data, name='client_table_data'),
    path('api/delete/<str:model_name>/<int:pk>/', views.UniversalDeleteView.as_view(), name='universal_delete'),
]

