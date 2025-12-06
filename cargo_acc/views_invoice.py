from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
from .models import Product


def product_invoice_pdf(request, pk):
    # Получаем товар
    product = get_object_or_404(Product, pk=pk)

    # Рендерим HTML-шаблон накладной
    html = render_to_string(
        "invoice/product_invoice.html",
        {
            "product": product,
            "request": request,   # <— обязательно для build_absolute_uri в шаблоне
        }
    )

    # Генерация PDF
    pdf = HTML(
        string=html,
        base_url=request.build_absolute_uri('/')
    ).write_pdf()

    # Возвращаем PDF в браузер
    response = HttpResponse(pdf, content_type="application/pdf")
    response['Content-Disposition'] = (
        f'inline; filename="invoice_{product.product_code}.pdf"'
    )
    return response
