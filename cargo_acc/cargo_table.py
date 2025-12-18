# cargo_acc/cargo_table.py

from django.contrib.auth.decorators import login_required
from django.db.models import Count, OuterRef, Subquery, IntegerField, Value, Q
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from cargo_acc.company_utils import get_user_company, get_log_meta
from cargo_acc.models import SystemActionLog
from cargo_acc.models import Cargo, Product


@login_required
def cargos_page(request):
    return render(request, "cargo_table.html", {"role": getattr(request.user, "role", "")})


@require_GET
@login_required
def cargos_table_view(request):
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
        "warehouse", "cargo_status", "packaging_type"
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
            Q(warehouse__name__icontains=search) |
            Q(cargo_status__name__icontains=search) |
            Q(packaging_type__name__icontains=search)
        )

    # SORTING
    SORTABLE = {
        "cargo_code": "cargo_code",
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
