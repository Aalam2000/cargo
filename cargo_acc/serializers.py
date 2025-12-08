# cargo_acc/serializers.py
from rest_framework import serializers

from .models import *


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'


class ClientSerializer(serializers.ModelSerializer):
    company = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Client
        fields = ['id', 'client_code', 'company', 'description']


class WarehouseSerializer(serializers.ModelSerializer):
    company = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Warehouse
        fields = ['id', 'name', 'address', 'company']


class CargoTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CargoType
        fields = '__all__'
        read_only_fields = ["company"]


class CargoStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = CargoStatus
        fields = '__all__'
        read_only_fields = ["company"]


class PackagingTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackagingType
        fields = '__all__'
        read_only_fields = ["company"]


class AccrualTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccrualType
        fields = '__all__'
        read_only_fields = ["company"]


class PaymentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentType
        fields = '__all__'
        read_only_fields = ["created_at", "company"]


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = '__all__'


class QRScanSerializer(serializers.ModelSerializer):
    class Meta:
        model = QRScan
        fields = '__all__'


# serializers.py
class ProductSerializer(serializers.ModelSerializer):
    images = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    # Клиент
    client_id = serializers.PrimaryKeyRelatedField(
        read_only=True
    )
    client_code = serializers.SlugRelatedField(
        slug_field='client_code',
        source='client',
        read_only=True
    )

    # Компания
    company_id = serializers.PrimaryKeyRelatedField(
        read_only=True
    )
    company_name = serializers.SlugRelatedField(
        slug_field='name',
        source='company',
        read_only=True
    )

    # Склад
    warehouse_id = serializers.PrimaryKeyRelatedField(
        read_only=True
    )
    warehouse_name = serializers.SlugRelatedField(
        slug_field='name',
        source='warehouse',
        read_only=True
    )

    # Тип груза
    cargo_type_id = serializers.PrimaryKeyRelatedField(
        read_only=True
    )
    cargo_type_name = serializers.SlugRelatedField(
        slug_field='name',
        source='cargo_type',
        read_only=True
    )

    # Статус груза
    cargo_status_id = serializers.PrimaryKeyRelatedField(
        read_only=True
    )
    cargo_status_name = serializers.SlugRelatedField(
        slug_field='name',
        source='cargo_status',
        read_only=True
    )

    # Тип упаковки
    packaging_type_id = serializers.PrimaryKeyRelatedField(
        read_only=True
    )
    packaging_type_name = serializers.SlugRelatedField(
        slug_field='name',
        source='packaging_type',
        read_only=True
    )

    class Meta:
        model = Product
        fields = [
            'id', 'product_code', 'record_date', 'cargo_description', 'comment',
            'departure_place', 'destination_place', 'weight', 'volume', 'cost',
            'insurance', 'shipping_date', 'delivery_date',
            'images',  # ManyToMany (read_only)
            # Для клиентов
            'client_id', 'client_code',
            # Для компании
            'company_id', 'company_name',
            # Для склада
            'warehouse_id', 'warehouse_name',
            # Для типа груза
            'cargo_type_id', 'cargo_type_name',
            # Для статуса груза
            'cargo_status_id', 'cargo_status_name',
            # Для типа упаковки
            'packaging_type_id', 'packaging_type_name',
            # QR на фото
            'qr_code', 'qr_created_at',

        ]


class CargoSerializer(serializers.ModelSerializer):
    products = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='product_code'
    )
    images = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='id'
    )
    client = serializers.StringRelatedField()
    cargo_status = serializers.StringRelatedField()
    packaging_type = serializers.StringRelatedField()

    class Meta:
        model = Cargo
        fields = '__all__'
        read_only_fields = ["company"]


class CarrierCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = CarrierCompany
        fields = '__all__'
        read_only_fields = ["company"]


class VehicleSerializer(serializers.ModelSerializer):
    carrier_company = serializers.StringRelatedField()

    class Meta:
        model = Vehicle
        fields = '__all__'


class TransportBillSerializer(serializers.ModelSerializer):
    cargos = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    vehicle = serializers.StringRelatedField()
    carrier_company = serializers.StringRelatedField()

    class Meta:
        model = TransportBill
        fields = '__all__'
        read_only_fields = ["company"]


class CargoMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = CargoMovement
        fields = '__all__'
        read_only_fields = ["company"]


class SystemActionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemActionLog
        fields = '__all__'
        read_only_fields = ["company"]
