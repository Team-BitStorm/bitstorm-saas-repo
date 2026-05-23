from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .openapi import auth_schema
from .serializers import (
    DetailResponseSerializer,
    LoginResponseSerializer,
    LoginSerializer,
    RefreshTokenSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


class FormJsonParserMixin:
    parser_classes = [JSONParser, FormParser]


@auth_schema(request=RegisterSerializer, summary="Register a new user")
class RegisterView(FormJsonParserMixin, generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


@auth_schema(
    request=LoginSerializer,
    responses={200: LoginResponseSerializer},
    summary="Login with email, phone, or CNP (returns JWT or 2FA challenge)",
)
class LoginView(FormJsonParserMixin, TokenObtainPairView):
    serializer_class = LoginSerializer


@auth_schema(request=TokenRefreshSerializer, summary="Refresh access token")
class RefreshView(FormJsonParserMixin, TokenRefreshView):
    serializer_class = TokenRefreshSerializer


@auth_schema(
    request=RefreshTokenSerializer,
    responses={200: DetailResponseSerializer},
    summary="Logout (blacklist refresh token)",
)
class LogoutView(FormJsonParserMixin, APIView):
    serializer_class = RefreshTokenSerializer
    # Logout is authorized by the refresh token, not the (possibly expired) access token.
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response(
                {"detail": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            RefreshToken(refresh).blacklist()
        except TokenError as exc:
            message = str(exc)
            if "blacklisted" in message.lower():
                return Response(
                    {"detail": "Successfully logged out."},
                    status=status.HTTP_200_OK,
                )
            return Response({"detail": message}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {"detail": "Successfully logged out."},
            status=status.HTTP_200_OK,
        )


@auth_schema(responses={200: UserSerializer}, summary="Current authenticated user")
class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
