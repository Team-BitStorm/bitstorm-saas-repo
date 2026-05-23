from rest_framework.permissions import BasePermission

from django.contrib.auth import get_user_model

User = get_user_model()


class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.CUSTOMER
        )


class IsProvider(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.PROVIDER
        )


class IsAuthenticatedRole(BasePermission):
    """Customer or provider with a valid JWT."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in (User.Role.CUSTOMER, User.Role.PROVIDER)
        )
