from django.urls import path

from . import views, views_2fa

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="auth-register"),
    path("login/", views.LoginView.as_view(), name="auth-login"),
    path("refresh/", views.RefreshView.as_view(), name="auth-refresh"),
    path("logout/", views.LogoutView.as_view(), name="auth-logout"),
    path("me/", views.MeView.as_view(), name="auth-me"),
    path(
        "password-reset/request/",
        views_2fa.PasswordResetRequestView.as_view(),
        name="auth-password-reset-request",
    ),
    path(
        "password-reset/confirm/",
        views_2fa.PasswordResetConfirmView.as_view(),
        name="auth-password-reset-confirm",
    ),
    path(
        "2fa/status/",
        views_2fa.TwoFactorStatusView.as_view(),
        name="auth-2fa-status",
    ),
    path(
        "2fa/method/",
        views_2fa.TwoFactorMethodView.as_view(),
        name="auth-2fa-method",
    ),
    path(
        "2fa/challenge/",
        views_2fa.TwoFactorChallengeView.as_view(),
        name="auth-2fa-challenge",
    ),
    path(
        "2fa/disable/",
        views_2fa.TwoFactorDisableView.as_view(),
        name="auth-2fa-disable",
    ),
    path(
        "2fa/totp/setup/",
        views_2fa.TotpSetupView.as_view(),
        name="auth-2fa-totp-setup",
    ),
    path(
        "2fa/totp/confirm/",
        views_2fa.TotpConfirmSetupView.as_view(),
        name="auth-2fa-totp-confirm",
    ),
    path(
        "2fa/totp/verify-login/",
        views_2fa.TotpVerifyLoginView.as_view(),
        name="auth-2fa-totp-verify-login",
    ),
    path(
        "2fa/sms/verify-login/",
        views_2fa.VerifySmsLoginView.as_view(),
        name="auth-2fa-sms-verify-login",
    ),
]
