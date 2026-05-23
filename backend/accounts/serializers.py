from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .phone_utils import normalize_phone
from .auth_utils import resolve_user_by_identifier, user_available_2fa_methods
from .two_factor import create_pre_auth_token

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    totp_configured = serializers.BooleanField(source="totp_confirmed", read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "birth_date",
            "role",
            "sms_2fa_enabled",
            "totp_configured",
            "date_joined",
        )
        read_only_fields = fields

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data.get("phone_number"):
            data["phone_number"] = normalize_phone(data["phone_number"])
        return data


def issue_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    refresh["role"] = user.role
    return {
        "requires_2fa": False,
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": UserSerializer(user).data,
    }


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = (
            "email",
            "password",
            "first_name",
            "last_name",
            "phone_number",
            "birth_date",
            "social_security_number",
            "role",
        )

    def validate_phone_number(self, value):
        return normalize_phone(value)

    def create(self, validated_data):
        password = validated_data.pop("password")
        email = validated_data.pop("email")
        return User.objects.create_user(email, password, **validated_data)


class RefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class LoginSerializer(TokenObtainPairSerializer):
    """Login with email, phone number, or CNP/SSN as identifier."""

    identifier = serializers.CharField(
        help_text="Email, phone number, or CNP/SSN registered on the account.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop(self.username_field, None)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        return token

    def validate(self, attrs):
        identifier = attrs.get("identifier", "").strip()
        password = attrs.get("password")
        user = resolve_user_by_identifier(identifier)

        if user is None or not user.check_password(password):
            raise serializers.ValidationError(
                {"detail": "No active account found with the given credentials."}
            )
        if not user.is_active:
            raise serializers.ValidationError({"detail": "User account is disabled."})

        self.user = user
        methods = user_available_2fa_methods(user)

        if not methods:
            refresh = self.get_token(user)
            return {
                "requires_2fa": False,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserSerializer(user).data,
            }

        return {
            "requires_2fa": True,
            "pre_auth_token": create_pre_auth_token(user.id),
            "available_2fa_methods": methods,
            "detail": (
                "Choose a verification method and POST /api/auth/2fa/challenge/ "
                "before entering your code."
            ),
        }


class TwoFactorStatusSerializer(serializers.Serializer):
    sms_2fa_enabled = serializers.BooleanField()
    totp_configured = serializers.BooleanField()
    phone_number = serializers.CharField(allow_blank=True)
    sms_available = serializers.BooleanField()
    available_2fa_methods = serializers.ListField(child=serializers.CharField())


class TwoFactorMethodSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=["sms", "totp"])
    enabled = serializers.BooleanField()


class TwoFactorChallengeSerializer(serializers.Serializer):
    pre_auth_token = serializers.CharField()
    method = serializers.ChoiceField(choices=["sms", "totp"])


class TotpConfirmSetupSerializer(serializers.Serializer):
    code = serializers.CharField(min_length=6, max_length=6)


class TotpVerifyLoginSerializer(serializers.Serializer):
    pre_auth_token = serializers.CharField()
    code = serializers.CharField(min_length=6, max_length=6)


class VerifySmsLoginSerializer(serializers.Serializer):
    pre_auth_token = serializers.CharField()
    code = serializers.CharField(min_length=6, max_length=6)


class PasswordResetRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=32)

    def validate_phone_number(self, value):
        return normalize_phone(value)


class PasswordResetConfirmSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=32)
    otp = serializers.CharField(min_length=6, max_length=6)
    new_password = serializers.CharField(min_length=8, write_only=True)

    def validate_phone_number(self, value):
        return normalize_phone(value)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class TwoFactorDisableSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Incorrect password.")
        return value


class DetailResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()


class TotpSetupResponseSerializer(serializers.Serializer):
    secret = serializers.CharField()
    provisioning_uri = serializers.CharField()
    detail = serializers.CharField()


class TotpConfirmResponseSerializer(serializers.Serializer):
    totp_configured = serializers.BooleanField()
    detail = serializers.CharField()


class TwoFactorMethodResponseSerializer(serializers.Serializer):
    method = serializers.CharField()
    enabled = serializers.BooleanField()
    available_2fa_methods = serializers.ListField(child=serializers.CharField())
    detail = serializers.CharField()


class TwoFactorChallengeResponseSerializer(serializers.Serializer):
    method = serializers.CharField()
    detail = serializers.CharField()
    otp_code = serializers.CharField(required=False)


class PasswordResetRequestResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
    phone_number = serializers.CharField(required=False)
    otp_code = serializers.CharField(required=False, allow_null=True)


class LoginResponseSerializer(serializers.Serializer):
    requires_2fa = serializers.BooleanField()
    access = serializers.CharField(required=False)
    refresh = serializers.CharField(required=False)
    user = UserSerializer(required=False)
    pre_auth_token = serializers.CharField(required=False)
    available_2fa_methods = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    detail = serializers.CharField(required=False)


class TokenPairResponseSerializer(serializers.Serializer):
    requires_2fa = serializers.BooleanField()
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()
