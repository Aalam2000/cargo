import os
import logging
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.http import HttpResponse
from weasyprint import HTML
from .models import Product


# ============================================================
#  НАСТРОЙКА ОТДЕЛЬНОГО ЛОГА ДЛЯ PDF
# ============================================================
LOG_PATH = "/var/log/invoice_debug.log"

# Полная перезапись лога при каждом открытии PDF
with open(LOG_PATH, "w", encoding="utf-8") as f:
    f.write("=== NEW PDF GENERATION SESSION ===\n")

logger = logging.getLogger("invoice_debug")
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler(LOG_PATH, mode="a", encoding="utf-8")
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
fh.setFormatter(formatter)

# чтобы не добавлялись дубль-хендлеры
if not logger.handlers:
    logger.addHandler(fh)


# ============================================================
#  ОСНОВНАЯ ФУНКЦИЯ
# ============================================================
def product_invoice_pdf(request, pk):
    logger.debug("=== START PDF GENERATION ===")

    # 1. Получаем товар
    product = get_object_or_404(Product, pk=pk)
    logger.debug(f"Product loaded: id={product.id}, code={product.product_code}")

    # 2. Формируем URL для статики
    domain = request.build_absolute_uri("/")
    static_logo = domain + static('img/logo.png')
    static_css = domain + static('css/invoice.css')

    logger.debug(f"domain = {domain}")
    logger.debug(f"static_logo = {static_logo}")
    logger.debug(f"static_css = {static_css}")

    # 3. Рендер HTML
    html = render_to_string(
        "invoice/product_invoice.html",
        {
            "product": product,
            "logo_url": static_logo,
            "css_url": static_css,
        }
    )
    logger.debug("HTML rendered successfully")

    # 4. Логируем HTML
    logger.debug("=== HTML START ===")
    logger.debug(html)
    logger.debug("=== HTML END ===")

    # 5. Генерация PDF
    try:
        logger.debug("Calling WeasyPrint HTML.write_pdf()...")

        pdf = HTML(
            string=html,
            base_url=request.build_absolute_uri("/")
        ).write_pdf()

        logger.debug("PDF generated successfully")

    except Exception as e:
        logger.error("PDF generation failed", exc_info=True)
        raise

    # 6. Возвращаем PDF
    logger.debug("=== END PDF GENERATION ===")

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="invoice_{product.product_code}.pdf"'
    return response
