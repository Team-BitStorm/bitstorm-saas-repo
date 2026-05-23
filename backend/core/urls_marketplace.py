from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views_marketplace as views

router = DefaultRouter()
router.register(
    "provider/offerings",
    views.ProviderOfferingViewSet,
    basename="provider-offering",
)
router.register(
    "provider/availability/rules",
    views.ProviderAvailabilityRuleViewSet,
    basename="provider-availability-rule",
)
router.register(
    "provider/availability/slots",
    views.ProviderAvailabilitySlotViewSet,
    basename="provider-availability-slot",
)
router.register(
    "provider/bookings",
    views.ProviderBookingViewSet,
    basename="provider-booking",
)
router.register(
    "provider/invoices",
    views.ProviderInvoiceViewSet,
    basename="provider-invoice",
)
router.register(
    "customer/availability",
    views.CustomerAvailabilityViewSet,
    basename="customer-availability",
)
router.register(
    "customer/bookings",
    views.CustomerBookingViewSet,
    basename="customer-booking",
)
router.register(
    "customer/invoices",
    views.CustomerInvoiceViewSet,
    basename="customer-invoice",
)
router.register(
    "marketplace/providers",
    views.MarketplaceProviderViewSet,
    basename="marketplace-provider",
)

urlpatterns = [
    path(
        "me/customer-profile/",
        views.MeCustomerProfileView.as_view(),
        name="me-customer-profile",
    ),
    path(
        "me/home-location/",
        views.MeHomeLocationView.as_view(),
        name="me-home-location",
    ),
    path(
        "me/provider-profile/",
        views.MeProviderProfileView.as_view(),
        name="me-provider-profile",
    ),
    path(
        "me/service-area/",
        views.MeServiceAreaView.as_view(),
        name="me-service-area",
    ),
    path(
        "provider/availability/generate/",
        views.ProviderGenerateSlotsView.as_view(),
        name="provider-generate-slots",
    ),
    path(
        "customer/payments/",
        views.CustomerPaymentListView.as_view(),
        name="customer-payments",
    ),
    path("", include(router.urls)),
]
