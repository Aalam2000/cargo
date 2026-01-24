# cargo_acc/services/code_generator.py

from __future__ import annotations

from django.db import transaction
from django.db.models import F

from cargo_acc.models import Company, Client, Product, Cargo


def _num(n: int, length: int) -> str:
    return str(n).zfill(length)


# === Клиент: PP000001 ===
@transaction.atomic
def generate_client_code(company: Company) -> str:
    """
    Атомарная генерация client_code, устойчивая к параллельным запросам.

    Алгоритм:
    - блокируем строку Company через select_for_update();
    - подбираем следующий код на основе company.prefix + zfill(company.client_counter + 1);
    - проверяем уникальность в cargo_acc_client.client_code;
    - если занят — увеличиваем счётчик и повторяем;
    - при успехе сохраняем company.client_counter.
    """
    # Важно: работаем с "свежей" строкой компании под блокировкой.
    locked_company = Company.objects.select_for_update().get(pk=company.pk)

    prefix = (locked_company.prefix or "").upper().strip()
    if not prefix:
        # Явно падаем, чтобы не генерировать мусорные коды.
        raise ValueError("Company.prefix пустой — невозможно сгенерировать client_code")

    # Стартуем со следующего значения
    counter = int(locked_company.client_counter or 0)

    while True:
        counter += 1
        candidate = f"{prefix}{_num(counter, 6)}"

        # Проверка уникальности по всей таблице (client_code уникален глобально)
        if not Client.objects.filter(client_code=candidate).exists():
            locked_company.client_counter = counter
            locked_company.save(update_fields=["client_counter"])
            return candidate


# === Товар клиента: <ClientCode>-000001 ===
@transaction.atomic
def generate_product_code(client: Client) -> str:
    client.product_counter += 1
    new_code = f"{client.client_code}-{_num(client.product_counter, 6)}"

    while Product.objects.filter(product_code=new_code, company=client.company).exists():
        client.product_counter += 1
        new_code = f"{client.client_code}-{_num(client.product_counter, 6)}"

    client.save(update_fields=["product_counter"])
    return new_code


# === Груз клиента: G-<ClientCode>-000001 ===
@transaction.atomic
def generate_cargo_code(client: Client) -> str:
    client.cargo_counter += 1
    new_code = f"G-{client.client_code}-{_num(client.cargo_counter, 6)}"

    while Cargo.objects.filter(cargo_code=new_code, company=client.company).exists():
        client.cargo_counter += 1
        new_code = f"G-{client.client_code}-{_num(client.cargo_counter, 6)}"

    client.save(update_fields=["cargo_counter"])
    return new_code
