from django.urls import path
from .views import (
    dialog_view,
    get_mac_address,
    tg_webhook,
    bot_help_view,
    platform_help_view,
)

urlpatterns = [
    path('', dialog_view, name='dialog'),
    path('get_mac/', get_mac_address, name='get_mac'),
    path('tg_webhook/', tg_webhook, name='tg_webhook'),
    path('bot-help/', bot_help_view, name='bot_help'),
    path('platform-help/', platform_help_view, name='platform_help'),
]