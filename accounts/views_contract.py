from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from cargodb.views import render_translated

@login_required
@require_GET
def contract_page(request):
    return render_translated(
        request=request,
        template_name="accounts/contract.html",
        context={},
        page_name="accounts/contract.html",
    )