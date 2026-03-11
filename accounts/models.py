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
        extra_fields.setdefault("role", "Admin")
        extra_fields.setdefault("access_level", "Company")
        extra_fields.setdefault("client_code", "ADMIN")
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ("Admin", "Администратор"),
        ("Operator", "Оператор"),
        ("WarehouseWorker", "Складской Работник"),
        ("Driver", "Водитель"),
        ("Client", "Клиент"),
    ]

    ACCESS_LEVEL_CHOICES = [
        ("Company", "Компания"),
        ("Branch", "Филиал"),
        ("Warehouse", "Склад"),
    ]

    # Учётные данные
    email = models.EmailField(unique=True)
    client_code = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        verbose_name="Код Клиента",
        help_text="Логин клиента. Используется для входа и фильтрации данных."
    )

    timezone = models.CharField(
        max_length=50,
        default='UTC',
        verbose_name='Часовой пояс',
        help_text='Например: Asia/Baku, Europe/Moscow, Asia/Shanghai'
    )
    CLIENT_TYPE_CHOICES = [
        ("individual", "Физическое лицо"),
        ("company", "Юридическое лицо"),
    ]

    client_type = models.CharField(
        max_length=20,
        choices=CLIENT_TYPE_CHOICES,
        default="individual",
        verbose_name="Тип клиента"
    )
    default_warehouse = models.ForeignKey(
        'cargo_acc.Warehouse',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users_default_warehouse',
        verbose_name="Склад по умолчанию"
    )

    default_cargo_type = models.ForeignKey(
        'cargo_acc.CargoType',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users_default_cargo_type',
        verbose_name="Тип груза по умолчанию"
    )

    default_cargo_status = models.ForeignKey(
        'cargo_acc.CargoStatus',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users_default_cargo_status',
        verbose_name="Статус груза по умолчанию"
    )

    default_packaging_type = models.ForeignKey(
        'cargo_acc.PackagingType',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users_default_packaging_type',
        verbose_name="Упаковка по умолчанию"
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
    inn = models.CharField(max_length=50, blank=True, default="Не указан")
    ogrn = models.CharField(max_length=50, blank=True, default="Не указан")
    representative = models.CharField(max_length=255, blank=True, default="Не указан")
    basis = models.CharField(max_length=255, blank=True, default="Не указан")
    # добавить в CustomUser перед contract_signed
    legal_address = models.CharField(max_length=255, blank=True, default="Не указан")
    actual_address = models.CharField(max_length=255, blank=True, default="Не указан")
    bank_name = models.CharField(max_length=255, blank=True, default="Не указан")
    bic = models.CharField(max_length=50, blank=True, default="Не указан")
    account = models.CharField(max_length=50, blank=True, default="Не указан")
    corr_account = models.CharField(max_length=50, blank=True, default="Не указан")
    company_name = models.CharField(max_length=255, blank=True, default="Не указано")

    contract_signed = models.BooleanField(default=False)
    sign_token = models.CharField(max_length=100, blank=True, null=True)

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

    # 🔗 Прямая связь с компанией
    company = models.ForeignKey(
        'cargo_acc.Company',
        on_delete=models.PROTECT,
        null=False,
        blank=False,
        related_name="users",
        verbose_name="Компания",
        help_text="Компания, к которой принадлежит пользователь (обязательное поле)"
    )

    # 🔗 Прямая связь с клиентом
    linked_client = models.ForeignKey(
        'cargo_acc.Client',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        help_text="Связанный объект клиента (для роли Client)."
    )

    # Настройки таблиц (JSON)
    table_settings = models.JSONField(default=dict, blank=True, null=True)

    USERNAME_FIELD = "email"
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
        if self.client_code:
            return f"{self.email} ({self.client_code})"
        return self.email

    @property
    def login(self):
        """Псевдоним: логин клиента — это client_code"""
        return self.client_code

    def save(self, *args, **kwargs):
        """Автоматическая синхронизация клиента и пользователя."""
        if self.email:
            self.email = self.__class__.objects.normalize_email(self.email)
        if self.client_code:
            self.client_code = str(self.client_code).strip().upper()

        from cargo_acc.models import Client

        if self.role == "Client" and self.linked_client:
            if not self.company_id and self.linked_client.company_id:
                self.company_id = self.linked_client.company_id
            if not self.client_code and self.linked_client.client_code:
                self.client_code = self.linked_client.client_code

        if self.role == "Client" and not self.linked_client and self.client_code:
            if not self.company_id:
                raise ValueError(
                    "Для пользователя с ролью Client обязательно должна быть указана company "
                    "до автосоздания/автопривязки клиента."
                )

            client = Client.objects.filter(
                company_id=self.company_id,
                client_code=self.client_code,
            ).first()

            if client:
                self.linked_client = client
            else:
                client = Client.objects.create(
                    client_code=self.client_code,
                    company_id=self.company_id,
                    description=f"Автоматически создан для {self.email}",
                )
                self.linked_client = client

        super().save(*args, **kwargs)
