# accounts/models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    """
    Кастомный менеджер:
    - нормализует email;
    - позволяет аутентифицироваться по email ИЛИ по client_code (логин);
      для этого переопределён get_by_natural_key().
    """

    def get_by_natural_key(self, username):
        """
        Делает возможным вход одним полем "username":
        если ввели email — найдём по email (без учёта регистра),
        иначе попытаемся найти по client_code (без учёта регистра).
        """
        # Пытаемся как email
        user = self.filter(email__iexact=username).first()
        if user:
            return user
        # Пытаемся как client_code (логин)
        return self.get(client_code__iexact=username)

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        # Нормализуем client_code (если передан)
        client_code = extra_fields.get("client_code")
        if client_code:
            extra_fields["client_code"] = str(client_code).strip().upper()

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.last_login = timezone.now()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "Admin")          # Роль для суперпользователя
        extra_fields.setdefault("access_level", "Company")  # Доступ на уровне компании

        # Дадим технический client_code суперпользователю, если не указан
        extra_fields.setdefault("client_code", "ADMIN")

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ("Admin", "Администратор"),
        ("Operator", "Оператор"),
        ("WarehouseWorker", "Складской Работник"),
        ("Driver", "Водитель"),
        ("Client", "Клиент"),  # Новая роль для кабинета клиента
    ]

    ACCESS_LEVEL_CHOICES = [
        ("Company", "Компания"),
        ("Branch", "Филиал"),
        ("Warehouse", "Склад"),
    ]

    # Учётные данные
    email = models.EmailField(unique=True)
    # client_code — это и есть "логин" клиента.
    # Делаем уникальным, разрешаем null (в PostgreSQL уникальность допускает несколько NULL),
    # чтобы операторы/админы могли существовать без кода клиента.
    client_code = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        verbose_name="Код Клиента",
        help_text="Логин клиента. Используется для входа и фильтрации данных."
    )

    # Профиль
    first_name = models.CharField(max_length=30, blank=True, default="Не указано")
    last_name = models.CharField(max_length=30, blank=True, default="Не указано")
    phone = models.CharField(max_length=15, blank=True, default="Не указано")
    telegram = models.CharField(max_length=30, blank=True, default="Не указано")
    whatsapp = models.CharField(max_length=30, blank=True, default="Не указано")
    website = models.URLField(blank=True, default="Не указано")
    country = models.CharField(max_length=50, blank=True, default="Не указано")
    city = models.CharField(max_length=50, blank=True, default="Не указано")
    address = models.CharField(max_length=255, blank=True, default="Не указано")

    # Статусы
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Роли и доступ
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="Operator")
    access_level = models.CharField(max_length=20, choices=ACCESS_LEVEL_CHOICES, default="Warehouse")
    assigned_object = models.CharField(
        max_length=50, blank=True, default="",
        help_text="Привязка к филиалу/складу (идентификатор или код)."
    )

    # Настройки таблиц (JSON)
    table_settings = models.JSONField(default=dict, blank=True, null=True)

    USERNAME_FIELD = "email"  # Базовое поле для Django-админки/форм
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = CustomUserManager()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        indexes = [
            models.Index(fields=["email"], name="idx_user_email_ci"),
            models.Index(fields=["client_code"], name="idx_user_client_code_ci"),
        ]

    def __str__(self):
        # Покажем и email, и логин-код (если есть)
        if self.client_code:
            return f"{self.email} ({self.client_code})"
        return self.email

    @property
    def login(self):
        """
        Псевдоним для ясности: логин клиента — это client_code.
        """
        return self.client_code

    def save(self, *args, **kwargs):
        # Нормализуем поля перед сохранением
        if self.email:
            self.email = self.__class__.objects.normalize_email(self.email)
        if self.client_code:
            self.client_code = str(self.client_code).strip().upper()
        super().save(*args, **kwargs)
