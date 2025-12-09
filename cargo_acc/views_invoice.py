from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.http import HttpResponse
from weasyprint import HTML
import logging
from .models import Product

log = logging.getLogger("pol")


def product_invoice_pdf(request, pk):
    log.debug("=== START PDF GENERATION ===")

    # --- Получаем товар ---
    product = get_object_or_404(Product, pk=pk)
    log.debug(f"Product loaded: id={product.id}, code={product.product_code}")

    # --- Рендер HTML ---


    domain = request.build_absolute_uri('/')  # https://bonablog.ru/
    static_logo = domain + static('img/logo.png')
    static_css = domain + static('css/invoice.css')

    html = render_to_string(
        "invoice/product_invoice.html",
        {
            "product": product,
            "logo_url": static_logo,
            "css_url": static_css,
        }
    )

    log.debug("HTML rendered successfully")

    # --- Логируем первые 500 символов HTML ---
    log.debug(f"HTML preview: {html[:500]}")

    # --- Пытаемся собрать PDF ---
    try:
        log.debug("Calling WeasyPrint HTML.write_pdf() ...")

        pdf = HTML(
            string=html,
            base_url=request.build_absolute_uri("/")  # НЕ трогаем (ты сказал всё раньше работало!)
        ).write_pdf()

        log.debug("PDF generated successfully")

    except Exception as e:
        log.error(f"PDF generation failed: {e}", exc_info=True)
        raise

    # --- Возврат PDF ---
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="invoice_{product.product_code}.pdf"'
    )

    log.debug("=== END PDF GENERATION ===")
    return response
