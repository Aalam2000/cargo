from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from cargo_acc.models import Company

@login_required
def profile_view(request):
    user = request.user
    role = getattr(user, 'role', None)
    can_edit = role in ['Admin', 'Operator', 'Client']

    if request.method == 'POST':
        user.client_type = request.POST.get('client_type', user.client_type)
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.phone = request.POST.get('phone', user.phone)
        user.telegram = request.POST.get('telegram', user.telegram)
        user.whatsapp = request.POST.get('whatsapp', user.whatsapp)

        if user.role == 'Client':
            user.inn = request.POST.get('inn', user.inn)
            user.ogrn = request.POST.get('ogrn', user.ogrn)
            user.representative = request.POST.get('representative', user.representative)
            user.basis = request.POST.get('basis', user.basis)

            # 🔒 Только админ может менять компанию и код клиента
            if request.user.role == 'Admin':
                company_id = request.POST.get('company_id')
                if company_id:
                    try:
                        user.company = Company.objects.get(id=company_id)
                    except Company.DoesNotExist:
                        pass

                new_code = request.POST.get('client_code')
                if new_code and new_code.strip():
                    user.client_code = new_code.strip().upper()

        user.save()
        messages.success(request, 'Профиль успешно обновлён.')
        return redirect('profile')

    return render(request, 'accounts/profile.html', {
        'user': user,
        'can_edit': can_edit,
        'companies': Company.objects.all() if user.role == 'Admin' else []
    })
