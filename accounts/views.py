# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from cargo_acc.models import Company, Warehouse, CargoType, CargoStatus, PackagingType
from cargo_acc.company_utils import get_user_company

@login_required
def profile_view(request):
    user = request.user
    role = getattr(user, 'role', None)
    can_edit = role in ['Admin', 'Operator', 'Client']
    company = get_user_company(request)

    if request.method == 'POST':
        # === Общие поля ===
        user.client_type = request.POST.get('client_type', user.client_type)
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.phone = request.POST.get('phone', user.phone)
        user.telegram = request.POST.get('telegram', user.telegram)
        user.whatsapp = request.POST.get('whatsapp', user.whatsapp)
        user.address = request.POST.get('address', user.address)

        # === Клиент ===
        if user.role == 'Client':
            user.inn = request.POST.get('inn', user.inn)
            user.company_name = request.POST.get('company_name', user.company_name)
            user.ogrn = request.POST.get('ogrn', user.ogrn)
            user.legal_address = request.POST.get('legal_address', user.legal_address)
            user.actual_address = request.POST.get('actual_address', user.actual_address)
            user.representative = request.POST.get('representative', user.representative)
            user.basis = request.POST.get('basis', user.basis)
            user.bank_name = request.POST.get('bank_name', user.bank_name)
            user.bic = request.POST.get('bic', user.bic)
            user.account = request.POST.get('account', user.account)
            user.corr_account = request.POST.get('corr_account', user.corr_account)

        # === Сотрудники ===
        if user.role in ['Admin', 'Operator', 'WarehouseWorker', 'Driver']:
            user.default_warehouse_id = request.POST.get('default_warehouse') or user.default_warehouse_id
            user.default_cargo_type_id = request.POST.get('default_cargo_type') or user.default_cargo_type_id
            user.default_cargo_status_id = request.POST.get('default_cargo_status') or user.default_cargo_status_id
            user.default_packaging_type_id = request.POST.get(
                'default_packaging_type') or user.default_packaging_type_id
            user.location = request.POST.get('location', user.location)
            user.work_hours = request.POST.get('work_hours', user.work_hours)
            user.notes = request.POST.get('notes', user.notes)

        user.save()

        messages.success(request, 'Профиль успешно обновлён.')
        return redirect('profile')

    return render(request, 'accounts/profile.html', {
        'user': user,
        'can_edit': can_edit,
        'companies': Company.objects.all() if user.role == 'Admin' else [],
        # === Добавляем справочники для сотрудников ===
        'warehouses': Warehouse.objects.filter(company=company),
        'cargo_types': CargoType.objects.filter(company=company),
        'cargo_statuses': CargoStatus.objects.filter(company=company),
        'packaging_types': PackagingType.objects.filter(company=company),
    })
