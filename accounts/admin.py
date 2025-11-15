from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser

    list_display = (
        "email", "client_code", "first_name", "last_name",
        "company", "role", "access_level", "is_staff", "is_active"
    )
    list_filter = ("role", "access_level", "is_staff", "is_active", "company")
    search_fields = ("email", "first_name", "last_name", "client_code")
    ordering = ("email",)

    fieldsets = (
        (None, {
            "fields": ("email", "password", "client_code", "company")
        }),
        ("Персональные данные", {
            "fields": (
                "first_name", "last_name", "phone", "telegram", "whatsapp",
                "website", "country", "city", "address", "timezone"
            )
        }),
        ("Реквизиты клиента", {
            "fields": (
                "client_type", "company_name", "inn", "ogrn", "representative", "basis",
                "legal_address", "actual_address", "bank_name", "bic",
                "account", "corr_account"
            )
        }),
        ("Разрешения и роли", {
            "fields": ("role", "access_level", "is_staff", "is_active", "is_superuser", "groups", "user_permissions")
        }),
        ("Статус договора", {
            "fields": ("contract_signed", "sign_token")
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email", "password1", "password2", "client_code", "company",
                "role", "access_level", "is_staff", "is_active"
            ),
        }),
    )
