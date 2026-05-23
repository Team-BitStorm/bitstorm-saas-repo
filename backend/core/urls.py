from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("geo-locations", views.GeoLocationViewSet, basename="geo-location")
router.register("languages", views.LanguageViewSet, basename="language")
router.register("user-profiles", views.UserProfileViewSet, basename="user-profile")
router.register(
    "provider-profiles", views.ProviderProfileViewSet, basename="provider-profile"
)
router.register("services", views.ServiceViewSet, basename="service")
router.register(
    "service-providers", views.ServiceProviderViewSet, basename="service-provider"
)
router.register("user-reviews", views.UserReviewViewSet, basename="user-review")
router.register(
    "provider-reviews", views.ProviderReviewViewSet, basename="provider-review"
)

urlpatterns = [
    path("", include(router.urls)),
]
