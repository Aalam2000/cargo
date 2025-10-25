# accounts/models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'Admin')  # Роль для суперпользователя
        extra_fields.setdefault('access_level', 'Company')  # Доступ на уровне компании
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('Admin', 'Администратор'),
        ('Operator', 'Оператор'),
        ('WarehouseWorker', 'Складской Работник'),
        ('Driver', 'Водитель'),
    ]

    ACCESS_LEVEL_CHOICES = [
        ('Company', 'Компания'),
        ('Branch', 'Филиал'),
        ('Warehouse', 'Склад'),
    ]

    email = models.EmailField(unique=True)
    client_code = models.CharField(max_length=20, blank=True, default='Не указано', verbose_name='Код Клиента')
    first_name = models.CharField(max_length=30, blank=True, default='Не указано')
    last_name = models.CharField(max_length=30, blank=True, default='Не указано')
    phone = models.CharField(max_length=15, blank=True, default='Не указано')
    telegram = models.CharField(max_length=30, blank=True, default='Не указано')
    whatsapp = models.CharField(max_length=30, blank=True, default='Не указано')
    website = models.URLField(blank=True, default='Не указано')
    country = models.CharField(max_length=50, blank=True, default='Не указано')
    city = models.CharField(max_length=50, blank=True, default='Не указано')
    address = models.CharField(max_length=255, blank=True, default='Не указано')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Новые поля для роли и уровня доступа
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Operator')
    access_level = models.CharField(max_length=20, choices=ACCESS_LEVEL_CHOICES, default='Warehouse')
    assigned_object = models.CharField(max_length=50, blank=True, default='')  # Привязка к филиалу/складу

    # Настройки таблиц (JSON)
    table_settings = models.JSONField(default=dict, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    def __str__(self):
        return self.email
