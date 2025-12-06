# cargo_acc/services/code_generator.py

from django.db import transaction
from cargo_acc.models import Company, Client, Product, Cargo


def _num(n: int, length: int) -> str:
    return str(n).zfill(length)


# === Клиент: PP000001 ===
@transaction.atomic
def generate_client_code(company: Company) -> str:
    company.client_counter += 1
    company.save(update_fields=["client_counter"])
    return f"{company.prefix.upper()}{_num(company.client_counter, 6)}"


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
