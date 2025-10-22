# cargodb/views.py
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from .forms import UserLoginForm
from django.contrib.auth.decorators import login_required

# @login_required
# def profile_view(request):
#     return render(request, 'accounts/profile.html')

@login_required
def dashboard_view(request):
    return render(request, 'cargo_acc/dashboard.html')

@login_required
def debugging_code_view(request):
    return render(request, 'cargo_acc/debugging_code.html')

@login_required
def orders_view(request):
    return render(request, 'cargo_acc/orders.html')

def index_view(request):
    return render(request, 'index.html')

def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('profile')
    else:
        form = UserLoginForm()
    return render(request, 'registration/login.html', {'form': form})


def home_view(request):
    return render(request, 'index.html')
