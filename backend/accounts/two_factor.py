import secrets
import string

import pyotp
from django.conf import settings
from django.core import signing
from django.core.cache import cache

PRE_AUTH_SALT = "accounts.pre_auth"
SMS_OTP_CACHE_PREFIX = "accounts.sms_otp"
PASSWORD_RESET_CACHE_PREFIX = "accounts.password_reset_otp"


def totp_issuer() -> str:
    return getattr(settings, "TOTP_ISSUER", "BitHealth")


def sms_otp_stub_expose() -> bool:
    return getattr(settings, "SMS_OTP_STUB_EXPOSE", True)


def _generate_numeric_otp(length: int = 6) -> str:
    return "".join(secrets.choice(string.digits) for _ in range(length))


def create_pre_auth_token(user_id: int) -> str:
    signer = signing.TimestampSigner(salt=PRE_AUTH_SALT)
    return signer.sign(str(user_id))


def load_user_id_from_pre_auth_token(token: str) -> int:
    max_age = getattr(settings, "PRE_AUTH_TIMEOUT_SECONDS", 300)
    signer = signing.TimestampSigner(salt=PRE_AUTH_SALT)
    user_id = signer.unsign(token, max_age=max_age)
    return int(user_id)


def issue_login_sms_otp(user_id: int) -> str:
    code = _generate_numeric_otp()
    timeout = getattr(settings, "SMS_OTP_TIMEOUT_SECONDS", 600)
    cache.set(f"{SMS_OTP_CACHE_PREFIX}:login:{user_id}", code, timeout=timeout)
    return code


def verify_login_sms_otp(user_id: int, code: str) -> bool:
    key = f"{SMS_OTP_CACHE_PREFIX}:login:{user_id}"
    expected = cache.get(key)
    if expected is None or expected != code.strip():
        return False
    cache.delete(key)
    return True


def issue_password_reset_otp(phone_number: str, user_id: int) -> str:
    code = _generate_numeric_otp()
    timeout = getattr(settings, "SMS_OTP_TIMEOUT_SECONDS", 600)
    cache.set(
        f"{PASSWORD_RESET_CACHE_PREFIX}:{phone_number}",
        {"code": code, "user_id": user_id},
        timeout=timeout,
    )
    return code


def verify_password_reset_otp(phone_number: str, code: str) -> int | None:
    key = f"{PASSWORD_RESET_CACHE_PREFIX}:{phone_number}"
    payload = cache.get(key)
    if not payload or payload.get("code") != code.strip():
        return None
    cache.delete(key)
    return payload["user_id"]


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def build_totp_provisioning_uri(secret: str, email: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name=totp_issuer())


def verify_totp_code(secret: str, code: str) -> bool:
    if not secret or not code:
        return False
    return pyotp.TOTP(secret).verify(code.strip(), valid_window=1)
