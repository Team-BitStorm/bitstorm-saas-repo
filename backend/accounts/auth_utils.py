from django.contrib.auth import get_user_model

from .cnp_utils import compute_cnp_hash
from .phone_utils import normalize_phone

User = get_user_model()


def resolve_user_by_identifier(identifier: str):
    """Find user by email, phone number, or CNP/SSN (exact match)."""
    value = (identifier or "").strip()
    if not value:
        return None

    user = User.objects.filter(email__iexact=value).first()
    if user:
        return user

    phone = normalize_phone(value)
    user = User.objects.filter(phone_number=phone).first()
    if user:
        return user
    if phone != value:
        user = User.objects.filter(phone_number=value).first()
        if user:
            return user

    return User.objects.filter(cnp_lookup_hash=compute_cnp_hash(value)).first()


def user_available_2fa_methods(user) -> list[str]:
    methods = []
    if user.sms_2fa_enabled and user.phone_number:
        methods.append(User.TwoFactorMethod.SMS)
    if user.totp_confirmed and user.totp_secret:
        methods.append(User.TwoFactorMethod.TOTP)
    return methods
