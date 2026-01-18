import jwt
from datetime import datetime, timedelta, timezone
from django.conf import settings


def build_cargochats_token(*, company_id: int, user_id: int) -> str:
    now = datetime.now(tz=timezone.utc)

    payload = {
        "company_id": company_id,
        "user_id": user_id,
        "issued_at": int(now.timestamp()),
        "expires_at": int((now + timedelta(minutes=10)).timestamp()),
    }

    token = jwt.encode(
        payload,
        settings.CARGOCHATS_JWT_SECRET,
        algorithm="HS256",
    )

    return token
