from django.urls import path
from .views import dialog_view, get_mac_address

urlpatterns = [
    path('', dialog_view, name='dialog'),
    path('get_mac/', get_mac_address, name='get_mac'),
]
