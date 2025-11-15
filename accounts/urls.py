# accounts/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views, views_profile


urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('profile/', views.profile_view, name='profile'),
    path('api/generate_contract/', views_profile.generate_contract, name='generate_contract'),
    path('api/send_sign_link/', views_profile.send_sign_link, name='send_sign_link'),
    path('api/generate_qr_payment/', views_profile.generate_qr_payment, name='generate_qr_payment'),
    path('contract/sign/<str:token>/', views_profile.sign_contract, name='sign_contract'),

    # только для администратора
    path('api/files/<str:username>/', views_profile.list_user_files, name='list_user_files'),
    path('api/files/<str:username>/<str:filename>/', views_profile.download_user_file, name='download_user_file'),
]
