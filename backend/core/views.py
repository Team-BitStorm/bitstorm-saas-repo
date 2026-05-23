from rest_framework import viewsets

from .models import (
    GeoLocation,
    Language,
    ProviderProfile,
    ProviderReview,
    Service,
    ServiceProvider,
    UserProfile,
    UserReview,
)
from .openapi import core_read_only_viewset
from .serializers import (
    GeoLocationSerializer,
    LanguageSerializer,
    ProviderProfileSerializer,
    ProviderReviewSerializer,
    ServiceProviderSerializer,
    ServiceSerializer,
    UserProfileSerializer,
    UserReviewSerializer,
)


@core_read_only_viewset
class GeoLocationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GeoLocation.objects.all()
    serializer_class = GeoLocationSerializer


@core_read_only_viewset
class LanguageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer


@core_read_only_viewset
class UserProfileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserProfile.objects.select_related(
        "user", "home_location"
    ).prefetch_related("user__languages")
    serializer_class = UserProfileSerializer


@core_read_only_viewset
class ProviderProfileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProviderProfile.objects.select_related(
        "user", "service_area"
    ).prefetch_related("user__languages")
    serializer_class = ProviderProfileSerializer


@core_read_only_viewset
class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    lookup_field = "slug"
    lookup_url_kwarg = "slug"


@core_read_only_viewset
class ServiceProviderViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ServiceProvider.objects.select_related(
        "provider__user",
        "provider__service_area",
        "service",
    ).prefetch_related("provider__user__languages")
    serializer_class = ServiceProviderSerializer


@core_read_only_viewset
class UserReviewViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserReview.objects.select_related(
        "reviewer",
        "provider__user",
        "provider__service_area",
    ).prefetch_related("reviewer__languages", "provider__user__languages")
    serializer_class = UserReviewSerializer


@core_read_only_viewset
class ProviderReviewViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProviderReview.objects.select_related(
        "reviewer",
        "customer",
    ).prefetch_related("reviewer__languages", "customer__languages")
    serializer_class = ProviderReviewSerializer
