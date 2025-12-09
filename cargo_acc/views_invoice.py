import os
import logging
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
from .models import Product


# ---------------------------------------------------------
# ЛОГ ФАЙЛ
# ---------------------------------------------------------
LOG_PATH = "/var/log/invoice_debug.log"
with open(LOG_PATH, "w", encoding="utf-8") as f:
    f.write("=== NEW PDF GENERATION SESSION ===\n")

logger = logging.getLogger("invoice_debug")
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler(LOG_PATH, mode="a", encoding="utf-8")
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
fh.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(fh)


# ---------------------------------------------------------
# ПУТИ К СТАТИКЕ НА ФАЙЛОВОЙ СИСТЕМЕ
# /app/web/static/css/invoice.css
# /app/web/static/img/logo.png
# ---------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_STATIC_ROOT = os.path.join(BASE_DIR, "web", "static")

CSS_FS_PATH = os.path.join(WEB_STATIC_ROOT, "css", "invoice.css")
LOGO_FS_PATH = os.path.join(WEB_STATIC_ROOT, "img", "logo.png")

CSS_FILE_URL = f"file://{CSS_FS_PATH}"
LOGO_FILE_URL = f"file://{LOGO_FS_PATH}"

BASE_FILE_URL = f"file://{WEB_STATIC_ROOT}"


def product_invoice_pdf(request, pk):
    logger.debug("=== START PDF GENERATION ===")

    product = get_object_or_404(Product, pk=pk)
    logger.debug(f"Product loaded: id={product.id}, code={product.product_code}")

    logger.debug(f"WEB_STATIC_ROOT = {WEB_STATIC_ROOT}")
    logger.debug(f"CSS_FS_PATH = {CSS_FS_PATH}")
    logger.debug(f"LOGO_FS_PATH = {LOGO_FS_PATH}")
    logger.debug(f"CSS_FILE_URL = {CSS_FILE_URL}")
    logger.debug(f"LOGO_FILE_URL = {LOGO_FILE_URL}")
    logger.debug(f"BASE_FILE_URL = {BASE_FILE_URL}")

    html = render_to_string(
        "invoice/product_invoice.html",
        {
            "product": product,
            "logo_url": LOGO_FILE_URL,
            "css_url": CSS_FILE_URL,
        }
    )

    logger.debug("HTML rendered successfully")
    logger.debug("=== HTML START ===")
    logger.debug(html)
    logger.debug("=== HTML END ===")

    try:
        logger.debug("Calling WeasyPrint HTML.write_pdf()...")

        pdf = HTML(
            string=html,
            base_url=BASE_FILE_URL,  # локальный file://, без HTTP
        ).write_pdf()

        logger.debug("PDF generated successfully")

    except Exception as e:
        logger.error("PDF generation failed", exc_info=True)
        raise

    logger.debug("=== END PDF GENERATION ===")

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="invoice_{product.product_code}.pdf"'
    )
    return response
