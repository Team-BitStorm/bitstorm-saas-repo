import hashlib
import hmac

from django.conf import settings


def compute_cnp_hash(cnp: str) -> str:
    """One-way HMAC for login lookup (CNP stored encrypted separately)."""
    value = (cnp or "").strip()
    if not value:
        return ""
    secret = getattr(settings, "CNP_LOOKUP_SECRET", None) or settings.SECRET_KEY
    return hmac.new(
        secret.encode("utf-8"),
        value.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
