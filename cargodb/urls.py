#  cargodb/urls.py

import logging

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include

from . import views

logger = logging.getLogger(__name__)

# ==============================
#  🔹 ОСНОВНЫЕ МАРШРУТЫ ПРОЕКТА
# ==============================

urlpatterns = [

    # === Главная страница ===
    path('', views.index_view, name='index'),  # http://localhost:8000/ → index.html (если не вошёл)
    path('home/', views.home_view, name='home'),  # http://localhost:8000/home/ → home.html (только после входа)
    path("cargo_table/", views.cargo_table_view, name="cargo_table"),  # страница таблицы грузов

    # === Подключение модулей ===
    path('bot/', include('chatgpt_ui.urls')),
    # === Админ-панель Django ===
    path("admin/", admin.site.urls),  # http://localhost:8000/admin/

    # === Аккаунты и авторизация ===
    path('accounts/', include('accounts.urls')),  # http://localhost:8000/accounts/...
    path('login/', auth_views.LoginView.as_view(), name='login'),  # http://localhost:8000/login/
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),  # http://localhost:8000/logout/
    path("home/balance/", views.client_balance, name="client_balance"),
    path('', include('cargo_acc.urls')),
    path("api/user_role/", views.api_user_role, name="api_user_role"),
]

# ==============================
#  🔹 ОБРАБОТКА СТАТИКИ И МЕДИА
# ==============================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# ==============================
#  🔹 ЛОГИРОВАНИЕ
# ==============================
