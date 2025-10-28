from django.shortcuts import redirect, render

def index_view(request):
    if request.user.is_authenticated:
        return redirect("cargo_table")  # если авторизован — сразу таблица грузов
    return render(request, "index.html")  # иначе обычная главная
