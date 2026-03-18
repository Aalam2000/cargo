from django.core.exceptions import PermissionDenied
from cargo_acc.models import SystemActionLog


def get_user_company(request):
    company = getattr(request, "company", None)
    if company is not None:
        return company

    user = getattr(request, "user", None)
    if user and hasattr(user, "company") and user.company is not None:
        return user.company

    raise PermissionDenied("Компания пользователя не определена")


def get_user_role(request):
    role = getattr(request, "role", None)
    if role is not None:
        return role

    user = getattr(request, "user", None)
    return getattr(user, "role", None)


def get_user_access_level(request):
    access_level = getattr(request, "access_level", None)
    if access_level is not None:
        return access_level

    user = getattr(request, "user", None)
    return getattr(user, "access_level", None)


def get_user_assigned_object(request):
    assigned_object = getattr(request, "assigned_object", None)
    if assigned_object is not None:
        return assigned_object

    user = getattr(request, "user", None)
    return getattr(user, "assigned_object", None)


def get_user_timezone(request):
    tz = getattr(request, "timezone", None)
    if tz:
        return tz

    user = getattr(request, "user", None)
    return getattr(user, "timezone", "UTC") or "UTC"


def get_user_table_settings(request):
    table_settings = getattr(request, "table_settings", None)
    if table_settings is not None:
        return table_settings

    user = getattr(request, "user", None)
    return getattr(user, "table_settings", None) or {}


def get_log_meta(model_name, object_id):
    logs = SystemActionLog.objects.filter(
        model_name=model_name,
        object_id=object_id
    ).order_by("id")

    create_log = logs.filter(action="create").first()
    update_log = logs.filter(action="update").last()

    return {
        "created_at": create_log.created_at if create_log else None,
        "created_by": (
            f"{create_log.operator.first_name} {create_log.operator.last_name}"
            if create_log and create_log.operator else ""
        ),
        "updated_at": update_log.created_at if update_log else None,
        "updated_by": (
            f"{update_log.operator.first_name} {update_log.operator.last_name}"
            if update_log and update_log.operator else ""
        ),
    }