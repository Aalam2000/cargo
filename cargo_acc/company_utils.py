from django.core.exceptions import PermissionDenied
from cargo_acc.models import SystemActionLog


def get_user_company(request):
    user = request.user
    if not user or not hasattr(user, "company") or user.company is None:
        raise PermissionDenied("Компания пользователя не определена")
    return user.company

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
