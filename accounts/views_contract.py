from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_GET

@login_required
@require_GET
def contract_page(request):
    return render(request, "accounts/contract.html")
