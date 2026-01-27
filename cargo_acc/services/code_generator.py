# cargo_acc/services/code_generator.py

from __future__ import annotations

from django.db import transaction, connection

from cargo_acc.models import Company, Client, Product, Cargo


def _num(n: int, length: int) -> str:
    return str(n).zfill(length)


# === Клиент: PP000001 ===
@transaction.atomic
def generate_client_code(company: Company) -> str:
    """
    Атомарная генерация client_code с заполнением "дыр".

    Гарантии:
    - блокируем строку Company (select_for_update) => параллельные запросы не дают дублей;
    - выбираем минимальный свободный номер (заполняем дырки);
    - client_counter повышаем только если выдали номер больше текущего counter.
    """
    locked_company = Company.objects.select_for_update().get(pk=company.pk)

    prefix = (locked_company.prefix or "").upper().strip()
    if not prefix:
        raise ValueError("Company.prefix пустой — невозможно сгенерировать client_code")

    # Важно: client_code уникален глобально, но номера ищем по префиксу компании.
    # Формат: <PREFIX><6 цифр>, например KH000010.
    regex = rf'^{prefix}[0-9]{{6}}$'
    like_prefix = f"{prefix}%"

    with connection.cursor() as cursor:
        cursor.execute(
            """
            WITH used AS (
                SELECT substring(client_code from '[0-9]{6}$')::int AS n
                FROM cargo_acc_client
                WHERE client_code LIKE %s
                  AND client_code ~ %s
            ),
            bounds AS (
                SELECT GREATEST(
                    COALESCE((SELECT max(n) FROM used), 0),
                    %s
                ) AS hi
            ),
            missing AS (
                SELECT gs.n
                FROM bounds b
                CROSS JOIN generate_series(1, b.hi) AS gs(n)
                LEFT JOIN used u ON u.n = gs.n
                WHERE u.n IS NULL
                ORDER BY gs.n
                LIMIT 1
            )
            SELECT
                COALESCE((SELECT n FROM missing), (SELECT hi + 1 FROM bounds)) AS next_n
            """,
            [like_prefix, regex, int(locked_company.client_counter or 0)],
        )
        next_n = int(cursor.fetchone()[0])

    client_code = f"{prefix}{_num(next_n, 6)}"

    # Подстраховка: если каким-то другим путём уже заняли (крайне редко),
    # просто повторим (сработает retry в create_client_with_user, но лучше тут).
    # Без бесконечного цикла: несколько шагов.
    for _ in range(5):
        if not Client.objects.filter(client_code=client_code).exists():
            if next_n > int(locked_company.client_counter or 0):
                locked_company.client_counter = next_n
                locked_company.save(update_fields=["client_counter"])
            return client_code

        next_n += 1
        client_code = f"{prefix}{_num(next_n, 6)}"

    raise RuntimeError("Не удалось подобрать уникальный client_code за 5 попыток")


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
