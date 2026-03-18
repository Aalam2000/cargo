from django.utils import timezone
import pytz


class UserContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.company = None
        request.role = None
        request.access_level = None
        request.assigned_object = None
        request.timezone = "UTC"
        request.table_settings = {}

        user = getattr(request, "user", None)
        if user and getattr(user, "is_authenticated", False):
            request.company = getattr(user, "company", None)
            request.role = getattr(user, "role", None)
            request.access_level = getattr(user, "access_level", None)
            request.assigned_object = getattr(user, "assigned_object", None)
            request.timezone = getattr(user, "timezone", "UTC") or "UTC"
            request.table_settings = getattr(user, "table_settings", None) or {}

        return self.get_response(request)


class UserTimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tzname = getattr(request, "timezone", "UTC") or "UTC"
        try:
            timezone.activate(pytz.timezone(tzname))
        except Exception:
            timezone.deactivate()
        return self.get_response(request)