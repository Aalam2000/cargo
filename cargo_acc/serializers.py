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

# serializers.py
class ProductSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True)  # Включаем связанные изображения
    client = serializers.SlugRelatedField(slug_field='client_code', queryset=Client.objects.all())
    company = serializers.SlugRelatedField(slug_field='name', queryset=Company.objects.all())
    warehouse = serializers.SlugRelatedField(slug_field='name', queryset=Warehouse.objects.all())
    cargo_type = serializers.SlugRelatedField(slug_field='name', queryset=CargoType.objects.all())
    cargo_status = serializers.SlugRelatedField(slug_field='name', queryset=CargoStatus.objects.all())
    packaging_type = serializers.SlugRelatedField(slug_field='name', queryset=PackagingType.objects.all())

    class Meta:
        model = Product
        fields = '__all__'

class CargoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cargo
        fields = '__all__'

class CarrierCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = CarrierCompany
        fields = '__all__'

class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = '__all__'

class TransportBillSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransportBill
        fields = '__all__'

class CargoMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = CargoMovement
        fields = '__all__'
