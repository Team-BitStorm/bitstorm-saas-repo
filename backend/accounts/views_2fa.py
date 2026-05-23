from django.contrib.auth import get_user_model
from django.core import signing
from rest_framework import permissions, status
from rest_framework.parsers import FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .phone_utils import normalize_phone
from .auth_utils import user_available_2fa_methods
from .openapi import tfa_auth_schema
from .serializers import (
    DetailResponseSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestResponseSerializer,
    PasswordResetRequestSerializer,
    TokenPairResponseSerializer,
    TotpConfirmResponseSerializer,
    TotpConfirmSetupSerializer,
    TotpSetupResponseSerializer,
    TotpVerifyLoginSerializer,
    TwoFactorChallengeResponseSerializer,
    TwoFactorChallengeSerializer,
    TwoFactorDisableSerializer,
    TwoFactorMethodResponseSerializer,
    TwoFactorMethodSerializer,
    TwoFactorStatusSerializer,
    VerifySmsLoginSerializer,
    issue_tokens_for_user,
)
from .two_factor import (
    build_totp_provisioning_uri,
    generate_totp_secret,
    issue_login_sms_otp,
    issue_password_reset_otp,
    load_user_id_from_pre_auth_token,
    sms_otp_stub_expose,
    verify_login_sms_otp,
    verify_password_reset_otp,
    verify_totp_code,
)

User = get_user_model()


class FormJsonParserMixin:
    parser_classes = [JSONParser, FormParser]


def _load_user_from_pre_auth(pre_auth_token: str):
    try:
        user_id = load_user_id_from_pre_auth_token(pre_auth_token)
    except signing.BadSignature:
        return None, Response(
            {"pre_auth_token": "Invalid or expired. Log in with password again."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except signing.SignatureExpired:
        return None, Response(
            {"pre_auth_token": "Expired. Log in with password again."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    user = User.objects.filter(pk=user_id).first()
    if not user:
        return None, Response(
            {"detail": "User not found."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return user, None


def _stub_otp_payload(code: str) -> dict:
    if sms_otp_stub_expose():
        return {
            "otp_code": code,
            "detail": "Stub SMS: use otp_code (no real SMS sent).",
        }
    return {"detail": "If this number is registered, a code was sent."}


@tfa_auth_schema(responses={200: TwoFactorStatusSerializer}, summary="2FA status")
class TwoFactorStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        methods = user_available_2fa_methods(user)
        serializer = TwoFactorStatusSerializer(
            {
                "sms_2fa_enabled": user.sms_2fa_enabled,
                "totp_configured": user.totp_confirmed,
                "phone_number": normalize_phone(user.phone_number),
                "sms_available": bool(user.phone_number),
                "available_2fa_methods": methods,
            }
        )
        return Response(serializer.data)


@tfa_auth_schema(
    request=TwoFactorMethodSerializer,
    responses={200: TwoFactorMethodResponseSerializer},
    summary="Enable or disable SMS or TOTP for login (both can be active)",
)
class TwoFactorMethodView(FormJsonParserMixin, APIView):
    serializer_class = TwoFactorMethodSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = TwoFactorMethodSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        method = serializer.validated_data["method"]
        enabled = serializer.validated_data["enabled"]
        user = request.user

        if method == User.TwoFactorMethod.SMS:
            if enabled and not user.phone_number:
                return Response(
                    {"phone_number": "Add a phone number before enabling SMS OTP."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.sms_2fa_enabled = enabled
            user.save(update_fields=["sms_2fa_enabled"])
        elif method == User.TwoFactorMethod.TOTP:
            if enabled and not user.totp_confirmed:
                return Response(
                    {"detail": "Complete authenticator setup before enabling TOTP."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not enabled:
                user.totp_confirmed = False
                user.totp_secret = ""
                user.save(update_fields=["totp_confirmed", "totp_secret"])
            # enabling totp is implicit after confirm; re-enable only if secret exists
            elif user.totp_secret:
                user.totp_confirmed = True
                user.save(update_fields=["totp_confirmed"])

        methods = user_available_2fa_methods(user)
        return Response(
            {
                "method": method,
                "enabled": enabled,
                "available_2fa_methods": methods,
                "detail": f"{method.upper()} login verification {'enabled' if enabled else 'disabled'}.",
            }
        )


@tfa_auth_schema(
    request=TwoFactorChallengeSerializer,
    responses={200: TwoFactorChallengeResponseSerializer},
    summary="Start 2FA challenge after login (pick SMS or TOTP)",
)
class TwoFactorChallengeView(FormJsonParserMixin, APIView):
    serializer_class = TwoFactorChallengeSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = TwoFactorChallengeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, error = _load_user_from_pre_auth(
            serializer.validated_data["pre_auth_token"]
        )
        if error:
            return error

        method = serializer.validated_data["method"]
        available = user_available_2fa_methods(user)
        if method not in available:
            return Response(
                {
                    "method": f"'{method}' is not enabled for this account.",
                    "available_2fa_methods": available,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if method == User.TwoFactorMethod.SMS:
            otp = issue_login_sms_otp(user.id)
            payload = {
                "method": method,
                "detail": "Enter the 6-digit code (stub: see otp_code).",
            }
            if sms_otp_stub_expose():
                payload["otp_code"] = otp
            return Response(payload)

        return Response(
            {
                "method": method,
                "detail": "Enter the 6-digit code from your authenticator app.",
            }
        )


@tfa_auth_schema(
    responses={200: TotpSetupResponseSerializer},
    summary="Generate TOTP secret and provisioning URI for QR",
)
class TotpSetupView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        secret = user.totp_secret or generate_totp_secret()
        if not user.totp_secret:
            user.totp_secret = secret
            user.totp_confirmed = False
            user.save(update_fields=["totp_secret", "totp_confirmed"])

        provisioning_uri = build_totp_provisioning_uri(secret, user.email)
        return Response(
            {
                "secret": secret,
                "provisioning_uri": provisioning_uri,
                "detail": "Scan provisioning_uri as QR, then confirm with a 6-digit code.",
            }
        )


@tfa_auth_schema(
    request=TotpConfirmSetupSerializer,
    responses={200: TotpConfirmResponseSerializer},
    summary="Confirm TOTP setup with 6-digit code",
)
class TotpConfirmSetupView(FormJsonParserMixin, APIView):
    serializer_class = TotpConfirmSetupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = TotpConfirmSetupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.totp_secret:
            return Response(
                {"detail": "Call setup first to generate a secret."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not verify_totp_code(user.totp_secret, serializer.validated_data["code"]):
            return Response(
                {"code": "Invalid authenticator code."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.totp_confirmed = True
        user.save(update_fields=["totp_confirmed"])
        return Response(
            {
                "totp_configured": True,
                "detail": "Authenticator configured. Enable it for login via POST /2fa/method/.",
            }
        )


@tfa_auth_schema(
    request=VerifySmsLoginSerializer,
    responses={200: TokenPairResponseSerializer},
    summary="Complete login after SMS OTP (step 3)",
)
class VerifySmsLoginView(FormJsonParserMixin, APIView):
    serializer_class = VerifySmsLoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifySmsLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, error = _load_user_from_pre_auth(
            serializer.validated_data["pre_auth_token"]
        )
        if error:
            return error

        if User.TwoFactorMethod.SMS not in user_available_2fa_methods(user):
            return Response(
                {"detail": "SMS verification is not enabled for this account."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not verify_login_sms_otp(user.id, serializer.validated_data["code"]):
            return Response(
                {"code": "Invalid or expired SMS code."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(issue_tokens_for_user(user))


@tfa_auth_schema(
    request=TotpVerifyLoginSerializer,
    responses={200: TokenPairResponseSerializer},
    summary="Complete login after authenticator code (step 3)",
)
class TotpVerifyLoginView(FormJsonParserMixin, APIView):
    serializer_class = TotpVerifyLoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = TotpVerifyLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, error = _load_user_from_pre_auth(
            serializer.validated_data["pre_auth_token"]
        )
        if error:
            return error

        if User.TwoFactorMethod.TOTP not in user_available_2fa_methods(user):
            return Response(
                {
                    "detail": "Authenticator verification is not enabled for this account."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not verify_totp_code(user.totp_secret, serializer.validated_data["code"]):
            return Response(
                {"code": "Invalid authenticator code."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(issue_tokens_for_user(user))


@tfa_auth_schema(
    request=PasswordResetRequestSerializer,
    responses={200: PasswordResetRequestResponseSerializer},
    summary="Request password reset OTP (SMS stub)",
)
class PasswordResetRequestView(FormJsonParserMixin, APIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone_number"]
        user = User.objects.filter(phone_number=phone).first()
        if not user:
            payload = {"detail": "If this number is registered, a code was sent."}
            if sms_otp_stub_expose():
                payload["otp_code"] = None
            return Response(payload)

        code = issue_password_reset_otp(phone, user.id)
        payload = _stub_otp_payload(code)
        payload["phone_number"] = phone
        return Response(payload)


@tfa_auth_schema(
    request=PasswordResetConfirmSerializer,
    responses={200: DetailResponseSerializer},
    summary="Confirm password reset with OTP",
)
class PasswordResetConfirmView(FormJsonParserMixin, APIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone_number"]
        user_id = verify_password_reset_otp(phone, serializer.validated_data["otp"])
        if user_id is None:
            return Response(
                {"otp": "Invalid or expired code."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = User.objects.filter(pk=user_id).first()
        if not user:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        return Response({"detail": "Password updated. You can log in now."})


@tfa_auth_schema(
    request=TwoFactorDisableSerializer,
    responses={200: DetailResponseSerializer},
    summary="Disable all 2FA (requires password)",
)
class TwoFactorDisableView(FormJsonParserMixin, APIView):
    serializer_class = TwoFactorDisableSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = TwoFactorDisableSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.sms_2fa_enabled = False
        user.totp_confirmed = False
        user.totp_secret = ""
        user.save(update_fields=["sms_2fa_enabled", "totp_confirmed", "totp_secret"])
        return Response({"detail": "Two-factor authentication disabled."})
