# accounts/serializers.py
from rest_framework import serializers
from .models import CustomUser

class UserSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company_name', read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'first_name', 'last_name', 'phone', 'telegram', 'whatsapp',
            'role', 'access_level', 'client_type', 'inn', 'ogrn', 'representative',
            'basis', 'company', 'company_name',
            'legal_address', 'actual_address',
            'bank_name', 'bic', 'account', 'corr_account',
            'client_code', 'contract_signed'
        ]
