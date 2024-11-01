# accounts/views.py
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import CustomUser
from .serializers import UserSerializer
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import UserLoginForm
from django.contrib import messages


@login_required
def profile_view(request):
    user = request.user

    # Проверяем роль и доступ
    role = getattr(user, 'role', None)

    # Убедимся, что role — это строка
    can_edit = role in ['Admin', 'Operator'] if isinstance(role, str) else False

    # Передаем данные в шаблон
    context = {
        'can_edit': can_edit,
        'user': user,
        'role_type': type(role).__name__  # Передаем тип роли в шаблон
    }

    if request.method == 'POST' and can_edit:
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.phone = request.POST.get('phone')

        if user.access_level == 'Company':
            user.client_code = request.POST.get('client_code')

        user.save()
        messages.success(request, 'Профиль успешно обновлён.')
        return redirect('profile')

    return render(request, 'accounts/profile.html', context)


@login_required
def dashboard_view(request):
    return render(request, 'cargo_acc/dashboard.html')


# Вход пользователя
def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('profile')
    else:
        form = UserLoginForm()
    return render(request, 'registration/login.html', {'form': form})


@login_required
def user_profile(request):
    return render(request, 'accounts/profile.html', {'user': request.user})


@api_view(['GET'])
def user_list(request):
    users = CustomUser.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)
