import requests
from datetime import date
from cargo_acc.models import CurrencyRate
from xml.etree import ElementTree as ET
import re


# ВАЛЮТЫ КЛИЕНТОВ. USD НЕ ВХОДИТ.
CURRENCIES = ["RUB", "CNY", "EUR", "TRY"]


# ==========================================================
# Сохраняем КУРС USD → ВАЛЮТА
# ==========================================================

def save_rate(currency, client_rate):
    obj = CurrencyRate.objects.filter(
        currency=currency,
        date=date.today()
    ).first()

    if obj:
        # обновляем только официальный курс
        obj.rate = client_rate
        obj.save(update_fields=["rate"])
    else:
        # создаём новую запись, ручной курс НЕ трогаем
        CurrencyRate.objects.create(
            currency=currency,
            date=date.today(),
            rate=client_rate
        )



# ==========================================================
# 1) NBU — EUR, CNY, TRY (RUB НЕТ)
#    ДАЁТ "ВАЛЮТА → UAH"
#    Нужно "USD → ВАЛЮТА"
# ==========================================================

def fetch_from_nbu(currency):
    if currency == "RUB":
        return None  # RUB в NBU отсутствует

    url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"
    r = requests.get(url, timeout=5)
    if r.status_code != 200:
        return None

    data = r.json()

    codes = {
        "EUR": 978,
        "CNY": 156,
        "TRY": 949,
        "USD": 840,
    }

    if currency not in codes:
        return None

    usd = next((x for x in data if x["r030"] == 840), None)
    cur = next((x for x in data if x["r030"] == codes[currency]), None)

    if not usd or not cur:
        return None

    # NBU формат:
    # cur["rate"] = VAL → UAH
    # usd["rate"] = USD → UAH
    #
    # нам нужно USD → VAL:
    #
    # 1 USD = (USD→UAH) / (VAL→UAH)

    return usd["rate"] / cur["rate"]


# ==========================================================
# 2) CBR — RUB, EUR, CNY, TRY
#    ДАЁТ "ВАЛЮТА → RUB"
#    Нужно "USD → ВАЛЮТА"
# ==========================================================

def fetch_from_cbr(currency):
    url = "https://www.cbr.ru/scripts/XML_daily.asp"
    r = requests.get(url, timeout=5)
    if r.status_code != 200:
        return None

    root = ET.fromstring(r.content)

    codes = {
        "EUR": "978",
        "CNY": "156",
        "TRY": "949"
        # RUB не нужен через код — считаем через доллар
    }

    usd_rub = None
    cur_rub = None

    for item in root.findall("Valute"):
        num = item.find("NumCode").text
        value = float(item.find("Value").text.replace(",", "."))
        nominal = int(item.find("Nominal").text)
        rub_value = value / nominal  # VAL → RUB

        if num == "840":
            usd_rub = rub_value  # USD → RUB

        if currency in codes and num == codes[currency]:
            cur_rub = rub_value  # VAL → RUB

    if usd_rub is None:
        return None

    # RUB:
    if currency == "RUB":
        return usd_rub  # USD → RUB

    # EUR, CNY, TRY:
    if cur_rub is None:
        return None

    # USD → ВАЛЮТА = (USD→RUB) / (VAL→RUB)
    return usd_rub / cur_rub


# ==========================================================
# 3) GOOGLE FINANCE — fallback
#    ДАЁТ "VAL → USD"
#    Нужно "USD → VAL"
# ==========================================================

def fetch_from_google(currency):
    url = f"https://www.google.com/finance/quote/{currency}-USD"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
    if r.status_code != 200:
        return None

    m = re.search(r'"data-last-price":"([\d\.]+)"', r.text)
    if not m:
        return None

    val_to_usd = float(m.group(1))
    return 1 / val_to_usd  # USD → VAL


# ==========================================================
# 4) YAHOO FINANCE — fallback
# ==========================================================

def fetch_from_yahoo(currency):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{currency}USD=X?interval=1d"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
    if r.status_code != 200:
        return None

    try:
        val_to_usd = r.json()["chart"]["result"][0]["meta"]["regularMarketPrice"]
        return 1 / val_to_usd
    except:
        return None


# ==========================================================
# Основной загрузчик
# ==========================================================

SOURCES = [
    fetch_from_nbu,
    fetch_from_cbr,
    fetch_from_google,
    fetch_from_yahoo,
]


def update_all_rates():
    results = {}

    for cur in CURRENCIES:

        rate = None

        for fn in SOURCES:
            try:
                rate = fn(cur)
            except:
                continue

            if rate:
                save_rate(cur, rate)
                results[cur] = rate
                break

        if rate is None:
            results[cur] = "ERROR"

    return results
