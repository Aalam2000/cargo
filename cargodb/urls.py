#cargodb/urls.py
from django.contrib import admin
from django.urls import path, include
from home import views as home_views  # импорт для index_view
from . import views  # импорт для других представлений (profile и dashboard)
from django.contrib.auth import views as auth_views
import logging
from django.conf import settings
from django.conf.urls.static import static

logger = logging.getLogger(__name__)

urlpatterns = [
    path('', home_views.index_view, name='index'),  # Для главной страницы
    path("admin/", admin.site.urls),
    path('accounts/', include('accounts.urls')),    # Подключаем все маршруты для приложения ccounts
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('debugging_code/', views.debugging_code_view, name='debugging_code'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('orders/', views.orders_view, name='orders'),
    path('cargo_acc/', include('cargo_acc.urls')),  # Подключаем все маршруты для приложения cargo_acc
    path('chatgpt_ui/', include('chatgpt_ui.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

logger.info("Запрос на маршрут был обработан!")