# cargo_acc/serializers.py
from rest_framework import serializers

from .models import *


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'


class ClientSerializer(serializers.ModelSerializer):
    company = serializers.SlugRelatedField(queryset=Company.objects.all(), slug_field='name')

    class Meta:
        model = Client
        fields = ['id', 'client_code', 'company', 'description']

    def create(self, validated_data):
        company_name = validated_data.pop('company')
        company, created = Company.objects.get_or_create(name=company_name)
        client = Client.objects.create(company=company, **validated_data)
        return client


class WarehouseSerializer(serializers.ModelSerializer):
    company = serializers.SlugRelatedField(queryset=Company.objects.all(), slug_field='name')

    class Meta:
        model = Warehouse
        fields = ['id', 'name', 'address', 'company']

    def create(self, validated_data):
        company = validated_data.pop('company')
        warehouse = Warehouse.objects.create(company=company, **validated_data)
        return warehouse


class CargoTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CargoType
        fields = '__all__'


class CargoStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = CargoStatus
        fields = '__all__'


class PackagingTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackagingType
        fields = '__all__'


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
        queryset=Client.objects.all(),
        source='client',
        required=False
    )
    client_code = serializers.SlugRelatedField(
        slug_field='client_code',
        source='client',
        read_only=True
    )

    # Компания
    company_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        source='company',
        required=False
    )
    company_name = serializers.SlugRelatedField(
        slug_field='name',
        source='company',
        read_only=True
    )

    # Склад
    warehouse_id = serializers.PrimaryKeyRelatedField(
        queryset=Warehouse.objects.all(),
        source='warehouse',
        required=False
    )
    warehouse_name = serializers.SlugRelatedField(
        slug_field='name',
        source='warehouse',
        read_only=True
    )

    # Тип груза
    cargo_type_id = serializers.PrimaryKeyRelatedField(
        queryset=CargoType.objects.all(),
        source='cargo_type',
        required=False
    )
    cargo_type_name = serializers.SlugRelatedField(
        slug_field='name',
        source='cargo_type',
        read_only=True
    )

    # Статус груза
    cargo_status_id = serializers.PrimaryKeyRelatedField(
        queryset=CargoStatus.objects.all(),
        source='cargo_status',
        required=False
    )
    cargo_status_name = serializers.SlugRelatedField(
        slug_field='name',
        source='cargo_status',
        read_only=True
    )

    # Тип упаковки
    packaging_type_id = serializers.PrimaryKeyRelatedField(
        queryset=PackagingType.objects.all(),
        source='packaging_type',
        required=False
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
            'insurance', 'dimensions', 'shipping_date', 'delivery_date',
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


class CarrierCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = CarrierCompany
        fields = '__all__'


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


class CargoMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = CargoMovement
        fields = '__all__'

class CargoStatusLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CargoStatusLog
        fields = '__all__'
