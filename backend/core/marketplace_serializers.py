from django.contrib.auth import get_user_model
from django.db.models import Min
from rest_framework import serializers

from .models import (
    AvailabilityCustomer,
    AvailabilityProvider,
    AvailabilityRule,
    FactBooking,
    FactPayment,
    GeoLocation,
    Invoice,
    ProviderProfile,
    ProviderReview,
    Service,
    ServiceProvider,
    UserProfile,
    UserReview,
)
from .serializers import GeoLocationSerializer, LanguageSerializer, ServiceSerializer


def _canonical_services(active_only: bool = True):
    """Deduplicated service queryset: one row per unique name (lowest PK wins)."""
    qs = Service.objects.filter(
        id__in=Service.objects.values("name")
        .annotate(min_id=Min("id"))
        .values("min_id")
    )
    if active_only:
        qs = qs.filter(is_active=True)
    return qs.order_by("name")


User = get_user_model()


class GeoLocationWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeoLocation
        fields = (
            "label",
            "address_line1",
            "address_line2",
            "city",
            "region",
            "postal_code",
            "country",
            "latitude",
            "longitude",
        )


class GeoLocationPublicSerializer(serializers.ModelSerializer):
    """
    Provider service-area location for public marketplace views.
    Exposes coordinates because the service area is a deliberate public
    business centroid (not a personal domicile).  Customer home addresses
    are protected separately via owner_user checks and are never served
    through this serializer.  Per §11.1 the personal account fields
    (email, phone, birth_date, CNP) are hidden at the User level; the
    provider's business coordinates are intentionally public.
    """

    class Meta:
        model = GeoLocation
        fields = ("id", "city", "region", "country", "latitude", "longitude")


class CustomerProfileSerializer(serializers.ModelSerializer):
    home_location = GeoLocationSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ("id", "avatar_url", "bio", "home_location")


class CustomerProfileWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ("avatar_url", "bio")


class ProviderProfileDetailSerializer(serializers.ModelSerializer):
    service_area = GeoLocationSerializer(read_only=True)

    class Meta:
        model = ProviderProfile
        fields = (
            "id",
            "display_name",
            "bio",
            "service_area",
            "travel_radius_km",
            "is_active",
        )
        read_only_fields = ("id", "is_active")


class ProviderProfileWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderProfile
        fields = ("display_name", "bio", "travel_radius_km", "is_active")


class ServiceOfferingSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(read_only=True)
    service_id = serializers.PrimaryKeyRelatedField(
        queryset=_canonical_services(),
        source="service",
        write_only=True,
    )

    class Meta:
        model = ServiceProvider
        fields = (
            "id",
            "service",
            "service_id",
            "provider_price",
            "duration_minutes",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "service", "created_at", "updated_at")


class AvailabilityRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailabilityRule
        fields = (
            "id",
            "weekday",
            "start_time",
            "end_time",
            "timezone",
            "is_active",
            "valid_from",
            "valid_until",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class AvailabilitySlotSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(read_only=True)
    service_id = serializers.PrimaryKeyRelatedField(
        queryset=_canonical_services(),
        source="service",
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = AvailabilityProvider
        fields = (
            "id",
            "rule",
            "service",
            "service_id",
            "starts_at",
            "ends_at",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "rule", "created_at", "updated_at")


class AvailabilitySlotBlockSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[
            AvailabilityProvider.Status.BLOCKED,
            AvailabilityProvider.Status.OPEN,
            AvailabilityProvider.Status.CANCELLED,
        ]
    )


class GenerateSlotsSerializer(serializers.Serializer):
    weeks = serializers.IntegerField(min_value=1, max_value=12, default=4)


class CustomerAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailabilityCustomer
        fields = (
            "id",
            "starts_at",
            "ends_at",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class BookingCustomerSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(read_only=True)
    provider_name = serializers.CharField(
        source="provider.display_name", read_only=True
    )
    visit_location = GeoLocationSerializer(read_only=True)

    class Meta:
        model = FactBooking
        fields = (
            "id",
            "provider",
            "provider_name",
            "service",
            "starts_at",
            "ends_at",
            "price",
            "price_min",
            "price_max",
            "travel_km",
            "travel_time_minutes",
            "duration_minutes",
            "status",
            "notes",
            "visit_location",
            "created_at",
            "updated_at",
            "confirmed_at",
            "completed_at",
            "cancelled_at",
        )


class BookingProviderSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(read_only=True)
    customer_email = serializers.EmailField(source="customer.email", read_only=True)
    customer_name = serializers.SerializerMethodField()
    visit_location = GeoLocationSerializer(read_only=True)

    class Meta:
        model = FactBooking
        fields = (
            "id",
            "customer",
            "customer_email",
            "customer_name",
            "service",
            "starts_at",
            "ends_at",
            "price",
            "price_min",
            "price_max",
            "travel_km",
            "travel_time_minutes",
            "duration_minutes",
            "status",
            "notes",
            "visit_location",
            "created_at",
            "updated_at",
            "confirmed_at",
            "completed_at",
            "cancelled_at",
        )

    def get_customer_name(self, obj):
        return obj.customer.get_full_name() or obj.customer.email


class BookingCreateSerializer(serializers.Serializer):
    provider_id = serializers.PrimaryKeyRelatedField(
        queryset=ProviderProfile.objects.filter(is_active=True),
        source="provider",
    )
    service_id = serializers.PrimaryKeyRelatedField(
        queryset=_canonical_services(),
        source="service",
    )
    provider_availability_id = serializers.PrimaryKeyRelatedField(
        queryset=AvailabilityProvider.objects.filter(
            status=AvailabilityProvider.Status.OPEN
        ),
        source="provider_availability",
    )
    customer_availability_id = serializers.PrimaryKeyRelatedField(
        queryset=AvailabilityCustomer.objects.all(),
        source="customer_availability",
        required=False,
        allow_null=True,
    )
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class ReviewCreateSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=10)
    comment = serializers.CharField(required=False, allow_blank=True, default="")


class InvoiceSerializer(serializers.ModelSerializer):
    booking_id = serializers.IntegerField(source="booking.id", read_only=True)

    class Meta:
        model = Invoice
        fields = (
            "id",
            "booking_id",
            "invoice_number",
            "subtotal",
            "tax",
            "total",
            "currency",
            "status",
            "issued_at",
            "due_at",
            "paid_at",
            "created_at",
            "updated_at",
        )


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FactPayment
        fields = (
            "id",
            "amount",
            "currency",
            "payment_method",
            "status",
            "external_reference",
            "paid_at",
            "created_at",
        )
        read_only_fields = fields


class PayInvoiceSerializer(serializers.Serializer):
    payment_method = serializers.ChoiceField(
        choices=FactPayment.Method.choices,
        default=FactPayment.Method.CARD,
    )


class MarketplaceProviderOfferingSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(read_only=True)

    class Meta:
        model = ServiceProvider
        fields = ("id", "service", "provider_price", "duration_minutes")


class MarketplaceProviderSerializer(serializers.ModelSerializer):
    languages = LanguageSerializer(source="user.languages", many=True, read_only=True)
    service_area = GeoLocationPublicSerializer(read_only=True)
    offerings = MarketplaceProviderOfferingSerializer(
        source="service_links", many=True, read_only=True
    )
    distance_km = serializers.SerializerMethodField()

    class Meta:
        model = ProviderProfile
        fields = (
            "id",
            "display_name",
            "bio",
            "service_area",
            "travel_radius_km",
            "is_active",
            "languages",
            "offerings",
            "distance_km",
        )

    def get_distance_km(self, obj):
        distance_map = self.context.get("distance_map", {})
        value = distance_map.get(obj.pk)
        if value is None:
            return None
        return str(value)


class MarketplaceSlotSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(read_only=True)

    class Meta:
        model = AvailabilityProvider
        fields = ("id", "service", "starts_at", "ends_at", "status")


class ApproxCustomerLocationSerializer(serializers.Serializer):
    """
    Single customer approximate location returned to provider callers.
    Coordinates are rounded to 2 decimal places (~1 km grid cell).
    """

    customer_id = serializers.IntegerField()
    approx_lat = serializers.FloatField()
    approx_lng = serializers.FloatField()
    radius_m = serializers.IntegerField()


class ApproxCustomerListItemSerializer(serializers.Serializer):
    """
    One entry in the provider's customer-location list used by the map view.
    Includes minimal booking context; never exposes full name, address string,
    or exact coordinates.
    """

    customer_id = serializers.IntegerField()
    first_name = serializers.CharField()
    approx_lat = serializers.FloatField()
    approx_lng = serializers.FloatField()
    radius_m = serializers.IntegerField()
    booking_count = serializers.IntegerField()


class BookingUserReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserReview
        fields = ("id", "rating", "comment", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class BookingProviderReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderReview
        fields = ("id", "rating", "comment", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")
