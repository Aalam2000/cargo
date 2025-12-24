# cargo_acc/cargo_table.py

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, OuterRef, Subquery, IntegerField, Q
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_POST, require_http_methods

from cargo_acc.company_utils import get_user_company, get_log_meta
from cargo_acc.models import Cargo, Product
from cargo_acc.models import SystemActionLog


@login_required
def cargos_page(request):
    return render(request, "cargo_acc/cargo_table.html", {"role": getattr(request.user, "role", "")})


@require_http_methods(["GET", "POST"])
@login_required
def cargos_table_view(request):
    # ==============================
    # GET — режимы для модалок
    # ==============================
    if request.method == "GET":
        mode = (request.GET.get("mode") or "").strip()
        company = get_user_company(request)
        user = request.user
        role = getattr(user, "role", "")

        # --- товары клиента для выбора в груз ---
        if mode == "cargo_products":
            client_id = (request.GET.get("client_id") or "").strip()
            cargo_id = (request.GET.get("cargo_id") or "").strip()

            # если client_id не передан — берём из груза
            if not client_id and cargo_id:
                try:
                    cargo = Cargo.objects.get(id=cargo_id, company=company)
                    client_id = str(cargo.client_id)
                except Cargo.DoesNotExist:
                    return JsonResponse({"error": "cargo not found"}, status=404)

            if not client_id:
                return JsonResponse({"error": "client_id required"}, status=400)

            if role == "Client":
                linked = getattr(user, "linked_client", None)
                if not linked or str(linked.id) != str(client_id):
                    return JsonResponse({"error": "forbidden"}, status=403)
            elif role not in ("Admin", "Operator"):
                return JsonResponse({"error": "forbidden"}, status=403)

            base_qs = Product.objects.filter(
                company=company,
                client_id=client_id,
            )

            free_qs = base_qs.filter(cargo_id__isnull=True)

            selected_qs = base_qs.none()
            if cargo_id:
                selected_qs = base_qs.filter(cargo_id=cargo_id)

            def serialize(qs):
                return list(
                    qs.order_by("product_code").values(
                        "id",
                        "product_code",
                        "cargo_description",
                        "cost",
                        "client_id",
                    )
                )

            client_code = None
            if cargo_id:
                client_code = Cargo.objects.filter(
                    id=cargo_id, company=company
                ).values_list("client__client_code", flat=True).first()

            cargo_data = {}
            if cargo_id:
                c = Cargo.objects.select_related(
                    "warehouse", "cargo_status", "packaging_type"
                ).get(id=cargo_id, company=company)

                cargo_data = {
                    "cargo_code": c.cargo_code,
                    "cargo_status_id": c.cargo_status_id,
                    "cargo_status": c.cargo_status.name if c.cargo_status else "",
                    "packaging_type_id": c.packaging_type_id,
                    "packaging_type": c.packaging_type.name if c.packaging_type else "",
                    "warehouse_id": c.warehouse_id,
                    "warehouse": c.warehouse.name if c.warehouse else "",
                }

            return JsonResponse({
                "client_id": int(client_id),
                "client_code": client_code,
                "free": serialize(free_qs),
                "selected": serialize(selected_qs),
                **cargo_data,
            })

        # --- старый режим (оставляем для совместимости) ---
        if mode == "available_products":
            client_id = (request.GET.get("client_id") or "").strip()
            if not client_id:
                return JsonResponse({"error": "client_id required"}, status=400)

            if role == "Client":
                linked = getattr(user, "linked_client", None)
                if not linked or str(linked.id) != str(client_id):
                    return JsonResponse({"error": "forbidden"}, status=403)
            elif role not in ("Admin", "Operator"):
                return JsonResponse({"error": "forbidden"}, status=403)

            products = list(
                Product.objects.filter(
                    company=company,
                    client_id=client_id,
                    cargo_id__isnull=True
                )
                .order_by("product_code")
                .values(
                    "id",
                    "product_code",
                    "cargo_description",
                    "cost",
                    "cargo_status_id",
                    "packaging_type_id",
                    "warehouse_id",
                )
            )
            return JsonResponse({"results": products})

            # если mode не задан — это обычный запрос таблицы
            # продолжаем выполнение ниже
            pass


    # POST-mode: создать груз и привязать выбранные товары
    if request.method == "POST":
        try:
            import json
            data = json.loads(request.body.decode("utf-8"))
        except Exception:
            return JsonResponse({"error": "bad json"}, status=400)

        company = get_user_company(request)
        user = request.user
        role = getattr(user, "role", "")

        client_id = data.get("client_id")
        cargo_id = data.get("cargo_id")
        cargo_code = (data.get("cargo_code") or "").strip()
        product_ids = data.get("product_ids") or []

        if not client_id:
            return JsonResponse({"error": "client_id required"}, status=400)

        if cargo_id:
            # EDIT MODE
            try:
                cargo = Cargo.objects.get(id=cargo_id, company=company)
            except Cargo.DoesNotExist:
                return JsonResponse({"error": "cargo not found"}, status=404)
        else:
            # CREATE MODE
            if not cargo_code:
                return JsonResponse({"error": "cargo_code required"}, status=400)

        if not isinstance(product_ids, list) or not product_ids:
            return JsonResponse({"error": "product_ids required"}, status=400)

        company = get_user_company(request)
        user = request.user
        role = getattr(user, "role", "")
        if role not in ("Admin", "Operator"):
            return JsonResponse({"error": "forbidden"}, status=403)

        uniq_ids = sorted({int(x) for x in product_ids if str(x).strip()})
        if not uniq_ids:
            return JsonResponse({"error": "product_ids required"}, status=400)

        if cargo_id:
            qs_products = Product.objects.filter(
                company=company,
                client_id=client_id,
                id__in=uniq_ids,
            ).filter(
                Q(cargo_id__isnull=True) | Q(cargo_id=cargo.id)
            )
        else:
            qs_products = Product.objects.filter(
                company=company,
                client_id=client_id,
                id__in=uniq_ids,
                cargo_id__isnull=True,
            )

        found_ids = list(qs_products.values_list("id", flat=True))
        if len(found_ids) != len(uniq_ids):
            missing = sorted(set(uniq_ids) - set(found_ids))
            return JsonResponse({"error": "some products not available", "missing": missing}, status=400)

        if not cargo_id:
            # CREATE — строгая проверка
            cargo_status_id = data.get("cargo_status_id")
            packaging_type_id = data.get("packaging_type_id")
            warehouse_id = data.get("warehouse_id")
        else:
            # EDIT — берём из POST
            warehouse_id = data.get("warehouse_id", cargo.warehouse_id)
            cargo_status_id = data.get("cargo_status_id", cargo.cargo_status_id)
            packaging_type_id = data.get("packaging_type_id", cargo.packaging_type_id)

        with transaction.atomic():
            if cargo_id:
                # --- EDIT ---
                # убираем товары, которые сняли
                Product.objects.filter(
                    company=company,
                    cargo_id=cargo.id
                ).exclude(id__in=uniq_ids).update(cargo_id=None)

                # добавляем новые
                Product.objects.filter(
                    company=company,
                    id__in=uniq_ids
                ).update(
                    cargo_id=cargo.id,
                    warehouse_id=warehouse_id,
                    cargo_status_id=cargo_status_id,
                )

                cargo.warehouse_id = warehouse_id
                cargo.cargo_status_id = cargo_status_id
                cargo.packaging_type_id = packaging_type_id
                cargo.updated_by = user
                cargo.updated_at = timezone.now()
                cargo.save(update_fields=[
                    "warehouse_id",
                    "cargo_status_id",
                    "packaging_type_id",
                    "updated_by",
                    "updated_at",
                ])

                action = "update"

            else:
                # --- CREATE ---
                cargo = Cargo.objects.create(
                    company=company,
                    client_id=client_id,
                    cargo_code=cargo_code,
                    cargo_status_id=cargo_status_id,
                    packaging_type_id=packaging_type_id,
                    warehouse_id=warehouse_id,
                    created_by=user,
                    updated_by=user,
                )

                Product.objects.filter(company=company, id__in=uniq_ids).update(
                    cargo_id=cargo.id,
                    warehouse_id=warehouse_id,
                    cargo_status_id=cargo_status_id,
                )
                action = "create"

            SystemActionLog.objects.create(
                company=company,
                model_name="Cargo",
                object_id=cargo.id,
                action=action,
                old_data={},
                new_data={
                    "client_id": int(client_id),
                    "cargo_code": cargo_code,
                    "cargo_status_id": int(cargo_status_id),
                    "packaging_type_id": int(packaging_type_id),
                    "warehouse_id": int(warehouse_id) if warehouse_id else None,
                    "product_ids": uniq_ids,
                },
                diff={},
                operator=user,
                ip=request.META.get("REMOTE_ADDR"),
            )

        return JsonResponse({"status": "ok", "cargo_id": cargo.id, "cargo_code": cargo.cargo_code})

    try:
        limit = int(request.GET.get("limit", 50))
        offset = int(request.GET.get("offset", 0))
    except Exception:
        return JsonResponse({"error": "bad pagination"}, status=400)

    sort_by = (request.GET.get("sort_by") or "cargo_code").strip()
    sort_dir = (request.GET.get("sort_dir") or "asc").strip()
    search = (request.GET.get("search") or "").strip()

    company = get_user_company(request)
    user = request.user
    role = getattr(user, "role", "")

    qs = Cargo.objects.filter(company=company).select_related(
        "client", "warehouse", "cargo_status", "packaging_type"
    )

    # Ограничение видимости для Client: только грузы, где есть его товары
    if role == "Client":
        linked = getattr(user, "linked_client", None)
        if not linked:
            return JsonResponse({"results": [], "total": 0, "has_more": False})
        cargo_ids = Product.objects.filter(
            company=company, client_id=linked.id, cargo_id__isnull=False
        ).values("cargo_id")
        qs = qs.filter(id__in=cargo_ids)
    elif role not in ("Admin", "Operator"):
        return JsonResponse({"results": [], "total": 0, "has_more": False})

    # Подсчёт товаров в грузе (без предположений про related_name)
    cnt_sq = Product.objects.filter(company=company, cargo_id=OuterRef("pk")) \
                 .values("cargo_id").annotate(c=Count("id")).values("c")[:1]
    qs = qs.annotate(products_count=Subquery(cnt_sq, output_field=IntegerField()))

    # Быстрый общий поиск
    if search:
        qs = qs.filter(
            Q(cargo_code__icontains=search) |
            Q(client__client_code__icontains=search) |
            Q(warehouse__name__icontains=search) |
            Q(cargo_status__name__icontains=search) |
            Q(packaging_type__name__icontains=search)
        )

    # -------- FILTERING (как товары) --------
    FILTERABLE = {
        "cargo_code": "cargo_code",
        "client": "client__client_code",
        "warehouse": "warehouse__name",
        "cargo_status": "cargo_status__name",
    }

    for key, value in request.GET.items():
        if not (key.startswith("filter[") and key.endswith("]")):
            continue
        val = (value or "").strip()
        if not val:
            continue

        field = key[7:-1]
        orm_field = FILTERABLE.get(field)
        if not orm_field:
            continue

        qs = qs.filter(**{f"{orm_field}__icontains": val})

    # SORTING
    SORTABLE = {
            "cargo_code": "cargo_code",
            "client": "client__client_code",
            "products_count": "products_count",
            "warehouse": "warehouse__name",
            "cargo_status": "cargo_status__name",
            "packaging_type": "packaging_type__name",
            "weight_total": "weight_total",
            "volume_total": "volume_total",
            "is_locked": "is_locked",
            "created_at": "created_at",
        }

    if sort_by == "record_date":
        field = "id"
    else:
        field = SORTABLE.get(sort_by, "cargo_code")

    if sort_dir == "desc":
        field = "-" + field
    qs = qs.order_by(field)

    total = qs.count()
    items = qs[offset: offset + limit]
    has_more = offset + limit < total

    results = []
    for c in items:
        meta = get_log_meta("Cargo", c.id)
        record_date = meta["created_at"].strftime("%Y-%m-%d") if meta.get("created_at") else ""

        results.append({
            "id": c.id,
            "client": c.client.client_code if c.client else "",
            "cargo_code": c.cargo_code,
            "record_date": record_date,
            "products_count": int(c.products_count or 0),
            "warehouse": c.warehouse.name if c.warehouse else "",
            "cargo_status": c.cargo_status.name if c.cargo_status else "",
            "packaging_type": c.packaging_type.name if c.packaging_type else "",
            "weight_total": str(c.weight_total) if c.weight_total is not None else "",
            "volume_total": str(c.volume_total) if c.volume_total is not None else "",
            "is_locked": bool(getattr(c, "is_locked", False)),
        })

    return JsonResponse({"results": results, "total": total, "has_more": has_more})


@require_POST
@login_required
def cargo_move_update_view(request):
    """
    Меняем warehouse/status у груза и синхронизируем у всех товаров в грузе.
    """
    try:
        import json
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "bad json"}, status=400)

    cargo_id = data.get("cargo_id")
    warehouse_id = data.get("warehouse_id", None)
    cargo_status_id = data.get("cargo_status_id", None)

    if not cargo_id:
        return JsonResponse({"error": "cargo_id required"}, status=400)

    company = get_user_company(request)

    try:
        cargo = Cargo.objects.select_related("warehouse", "cargo_status").get(id=cargo_id, company=company)
    except Cargo.DoesNotExist:
        return JsonResponse({"error": "cargo not found"}, status=404)

    old_data = {
        "warehouse_id": cargo.warehouse_id,
        "cargo_status_id": cargo.cargo_status_id,
    }

    changed = False

    if warehouse_id is not None and int(warehouse_id) != int(cargo.warehouse_id or 0):
        cargo.warehouse_id = int(warehouse_id)
        changed = True

    if cargo_status_id is not None and int(cargo_status_id) != int(cargo.cargo_status_id):
        cargo.cargo_status_id = int(cargo_status_id)
        changed = True

    if not changed:
        return JsonResponse({"status": "noop"})

    cargo.updated_by = request.user
    cargo.updated_at = timezone.now()
    cargo.save(update_fields=["warehouse_id", "cargo_status_id", "updated_by", "updated_at"])

    # синхронизация на товары (warehouse/status у товара NOT NULL)
    upd = {}
    if cargo.warehouse_id:
        upd["warehouse_id"] = cargo.warehouse_id
    if cargo.cargo_status_id:
        upd["cargo_status_id"] = cargo.cargo_status_id

    if upd:
        Product.objects.filter(company=company, cargo_id=cargo.id).update(**upd)

    new_data = {"warehouse_id": cargo.warehouse_id, "cargo_status_id": cargo.cargo_status_id}
    diff = {k: [old_data.get(k), new_data.get(k)] for k in new_data if old_data.get(k) != new_data.get(k)}

    SystemActionLog.objects.create(
        company=company,
        model_name="Cargo",
        object_id=cargo.id,
        action="update",
        old_data=old_data,
        new_data=new_data,
        diff=diff,
        operator=request.user,
        ip=request.META.get("REMOTE_ADDR"),
    )

    return JsonResponse({"status": "ok"})


@require_POST
@login_required
def cargo_lock_view(request):
    """
    Фиксируем/разрешаем изменение состава.
    """
    try:
        import json
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "bad json"}, status=400)

    cargo_id = data.get("cargo_id")
    lock = bool(data.get("lock", True))

    if not cargo_id:
        return JsonResponse({"error": "cargo_id required"}, status=400)

    company = get_user_company(request)

    try:
        cargo = Cargo.objects.get(id=cargo_id, company=company)
    except Cargo.DoesNotExist:
        return JsonResponse({"error": "cargo not found"}, status=404)

    old_data = {"is_locked": bool(getattr(cargo, "is_locked", False))}

    cargo.is_locked = lock
    cargo.locked_at = timezone.now() if lock else None
    cargo.locked_by = request.user if lock else None
    cargo.updated_by = request.user
    cargo.updated_at = timezone.now()
    cargo.save(update_fields=["is_locked", "locked_at", "locked_by", "updated_by", "updated_at"])

    new_data = {"is_locked": cargo.is_locked}
    diff = {"is_locked": [old_data["is_locked"], cargo.is_locked]}

    SystemActionLog.objects.create(
        company=company,
        model_name="Cargo",
        object_id=cargo.id,
        action="update",
        old_data=old_data,
        new_data=new_data,
        diff=diff,
        operator=request.user,
        ip=request.META.get("REMOTE_ADDR"),
    )

    return JsonResponse({"status": "ok", "is_locked": cargo.is_locked})
