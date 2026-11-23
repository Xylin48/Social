"""Local client-side status expiration, evaluated when profiles are viewed."""
from datetime import datetime, timedelta, timezone

STATUS_LIFETIME = timedelta(hours=48)


def visible_status(profile, now=None):
    value = profile.get("status") or ""
    if not value:
        return ""
    if profile.get("status_infinite"):
        return value
    raw = profile.get("status_set_at")
    if not raw:
        return ""
    try:
        started = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if started.tzinfo is None:
            return ""
        current = now or datetime.now(timezone.utc)
        if current < started or current - started >= STATUS_LIFETIME:
            return ""
    except (ValueError, TypeError, OverflowError):
        return ""
    return value
