from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .openapi import json_and_form_request
from .serializers import (
    EmailTokenObtainPairSerializer,
    RefreshTokenSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


class FormJsonParserMixin:
    parser_classes = [JSONParser, FormParser]


@json_and_form_request(RegisterSerializer)
class RegisterView(FormJsonParserMixin, generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


@json_and_form_request(EmailTokenObtainPairSerializer)
class LoginView(FormJsonParserMixin, TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer


@json_and_form_request(TokenRefreshSerializer)
class RefreshView(FormJsonParserMixin, TokenRefreshView):
    pass


@json_and_form_request(RefreshTokenSerializer)
class LogoutView(FormJsonParserMixin, APIView):
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


# for the current-logged user. maybe this calls for a rename
class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
