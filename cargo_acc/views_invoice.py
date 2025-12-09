import os
import time
import logging
import requests
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.http import HttpResponse
from weasyprint import HTML
from .models import Product


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


def product_invoice_pdf(request, pk):
    logger.debug("=== START PDF GENERATION ===")

    product = get_object_or_404(Product, pk=pk)
    logger.debug(f"Product loaded: id={product.id}, code={product.product_code}")

    static_logo = static('img/logo.png')
    static_css = static('css/invoice.css')

    logger.debug(f"static_logo = {static_logo}")
    logger.debug(f"static_css = {static_css}")

    html = render_to_string(
        "invoice/product_invoice.html",
        {
            "product": product,
            "logo_url": static_logo,
            "css_url": static_css,
        }
    )

    logger.debug("HTML rendered successfully")
    logger.debug("=== HTML START ===")
    logger.debug(html)
    logger.debug("=== HTML END ===")

    start = time.time()
    try:
        r_css = requests.get(request.build_absolute_uri(static_css), timeout=10)
        logger.debug(
            f"[CSS CHECK] status={r_css.status_code}, "
            f"len={len(r_css.content)}, "
            f"time={(time.time() - start):.2f}s"
        )
    except Exception as e:
        logger.debug(f"[CSS CHECK] ERROR: {e}")

    start = time.time()
    try:
        r_logo = requests.get(request.build_absolute_uri(static_logo), timeout=10)
        logger.debug(
            f"[LOGO CHECK] status={r_logo.status_code}, "
            f"len={len(r_logo.content)}, "
            f"time={(time.time() - start):.2f}s"
        )
    except Exception as e:
        logger.debug(f"[LOGO CHECK] ERROR: {e}")

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

    logger.debug("=== END PDF GENERATION ===")

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="invoice_{product.product_code}.pdf"'
    )
    return response
