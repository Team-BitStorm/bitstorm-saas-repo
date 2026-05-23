from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .booking_service import (
    cancel_booking,
    create_booking,
    pay_invoice,
    transition_booking,
)
from .geo_utils import haversine_km, location_has_coordinates
from .marketplace_serializers import (
    AvailabilityRuleSerializer,
    AvailabilitySlotBlockSerializer,
    AvailabilitySlotSerializer,
    BookingCreateSerializer,
    BookingCustomerSerializer,
    BookingProviderReviewSerializer,
    BookingProviderSerializer,
    BookingUserReviewSerializer,
    CustomerAvailabilitySerializer,
    CustomerProfileSerializer,
    CustomerProfileWriteSerializer,
    GenerateSlotsSerializer,
    GeoLocationWriteSerializer,
    InvoiceSerializer,
    MarketplaceProviderSerializer,
    MarketplaceSlotSerializer,
    PayInvoiceSerializer,
    PaymentSerializer,
    ProviderProfileDetailSerializer,
    ProviderProfileWriteSerializer,
    ReviewCreateSerializer,
    ServiceOfferingSerializer,
)
from .models import (
    AvailabilityCustomer,
    AvailabilityProvider,
    AvailabilityRule,
    FactBooking,
    FactPayment,
    Invoice,
    ProviderProfile,
    ProviderReview,
    ServiceProvider,
    UserProfile,
    UserReview,
)
from .openapi import customer_schema, marketplace_schema, me_schema, provider_schema
from .permissions import IsCustomer, IsProvider
from .serializers import GeoLocationSerializer
from .slot_service import generate_provider_slots

User = get_user_model()


def get_provider_profile(user) -> ProviderProfile:
    profile = getattr(user, "provider_profile", None)
    if profile is None:
        raise ValidationError(
            {"detail": "Provider profile not found. Complete onboarding first."}
        )
    return profile


def get_customer_profile(user) -> UserProfile:
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


@me_schema(summary="Get or update customer profile")
class MeCustomerProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, IsCustomer]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return CustomerProfileWriteSerializer
        return CustomerProfileSerializer

    def get_object(self):
        return get_customer_profile(self.request.user)


@me_schema(summary="Get or set customer home location (private domicile)")
class MeHomeLocationView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]

    @extend_schema(responses={200: GeoLocationSerializer})
    def get(self, request):
        profile = get_customer_profile(request.user)
        if not profile.home_location_id:
            return Response(
                {"detail": "Home location not set."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(GeoLocationSerializer(profile.home_location).data)

    @extend_schema(
        request=GeoLocationWriteSerializer, responses={200: GeoLocationSerializer}
    )
    def post(self, request):
        return self._save(request)

    @extend_schema(
        request=GeoLocationWriteSerializer, responses={200: GeoLocationSerializer}
    )
    def put(self, request):
        return self._save(request)

    @extend_schema(
        request=GeoLocationWriteSerializer, responses={200: GeoLocationSerializer}
    )
    def patch(self, request):
        return self._save(request, partial=True)

    def _save(self, request, partial=False):
        profile = get_customer_profile(request.user)
        if profile.home_location_id:
            serializer = GeoLocationWriteSerializer(
                profile.home_location, data=request.data, partial=partial
            )
        else:
            serializer = GeoLocationWriteSerializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        location = serializer.save(owner_user=request.user)
        profile.home_location = location
        profile.save(update_fields=["home_location"])
        return Response(GeoLocationSerializer(location).data)


@me_schema(summary="Get or update provider profile")
class MeProviderProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, IsProvider]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return ProviderProfileWriteSerializer
        return ProviderProfileDetailSerializer

    def get_object(self):
        profile, created = ProviderProfile.objects.get_or_create(
            user=self.request.user,
            defaults={
                "display_name": self.request.user.get_full_name()
                or self.request.user.email
            },
        )
        if created and self.request.user.role != User.Role.PROVIDER:
            raise ValidationError({"detail": "User is not a provider."})
        return profile


@me_schema(summary="Get or set provider public service area")
class MeServiceAreaView(APIView):
    permission_classes = [IsAuthenticated, IsProvider]

    @extend_schema(responses={200: GeoLocationSerializer})
    def get(self, request):
        profile = get_provider_profile(request.user)
        if not profile.service_area_id:
            return Response(
                {"detail": "Service area not set."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(GeoLocationSerializer(profile.service_area).data)

    @extend_schema(
        request=GeoLocationWriteSerializer, responses={200: GeoLocationSerializer}
    )
    def post(self, request):
        return self._save(request)

    @extend_schema(
        request=GeoLocationWriteSerializer, responses={200: GeoLocationSerializer}
    )
    def put(self, request):
        return self._save(request)

    @extend_schema(
        request=GeoLocationWriteSerializer, responses={200: GeoLocationSerializer}
    )
    def patch(self, request):
        return self._save(request, partial=True)

    def _save(self, request, partial=False):
        profile = get_provider_profile(request.user)
        if profile.service_area_id:
            serializer = GeoLocationWriteSerializer(
                profile.service_area, data=request.data, partial=partial
            )
        else:
            serializer = GeoLocationWriteSerializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        location = serializer.save()
        profile.service_area = location
        profile.save(update_fields=["service_area"])
        return Response(GeoLocationSerializer(location).data)


@extend_schema_view(
    list=provider_schema(summary="List my service offerings"),
    create=provider_schema(summary="Add a catalog service with my price"),
    retrieve=provider_schema(summary="Retrieve an offering"),
    update=provider_schema(summary="Update an offering"),
    partial_update=provider_schema(summary="Partially update an offering"),
    destroy=provider_schema(summary="Remove an offering"),
)
class ProviderOfferingViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsProvider]
    serializer_class = ServiceOfferingSerializer
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]

    def get_queryset(self):
        provider = get_provider_profile(self.request.user)
        return ServiceProvider.objects.filter(provider=provider).select_related(
            "service"
        )

    def perform_create(self, serializer):
        provider = get_provider_profile(self.request.user)
        serializer.save(provider=provider)


@extend_schema_view(
    list=provider_schema(summary="List my recurring availability rules"),
    create=provider_schema(summary="Create a recurring availability rule"),
    retrieve=provider_schema(summary="Retrieve a rule"),
    update=provider_schema(summary="Update a rule"),
    partial_update=provider_schema(summary="Partially update a rule"),
    destroy=provider_schema(summary="Delete a rule"),
)
class ProviderAvailabilityRuleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsProvider]
    serializer_class = AvailabilityRuleSerializer
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]

    def get_queryset(self):
        provider = get_provider_profile(self.request.user)
        return AvailabilityRule.objects.filter(provider=provider)

    def perform_create(self, serializer):
        provider = get_provider_profile(self.request.user)
        serializer.save(provider=provider)


@provider_schema(summary="Generate open slots from recurring rules")
class ProviderGenerateSlotsView(APIView):
    permission_classes = [IsAuthenticated, IsProvider]

    @extend_schema(
        request=GenerateSlotsSerializer,
        responses={201: AvailabilitySlotSerializer(many=True)},
    )
    def post(self, request):
        serializer = GenerateSlotsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        provider = get_provider_profile(request.user)
        slots = generate_provider_slots(
            provider, weeks=serializer.validated_data["weeks"]
        )
        return Response(
            AvailabilitySlotSerializer(slots, many=True).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    list=provider_schema(summary="List my availability slots"),
    create=provider_schema(summary="Add a one-off open slot"),
    retrieve=provider_schema(summary="Retrieve a slot"),
    destroy=provider_schema(summary="Delete an unbooked slot"),
)
class ProviderAvailabilitySlotViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsProvider]
    serializer_class = AvailabilitySlotSerializer
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):
        provider = get_provider_profile(self.request.user)
        qs = AvailabilityProvider.objects.filter(provider=provider).select_related(
            "service", "rule"
        )
        status_filter = self.request.query_params.get("status")
        from_param = self.request.query_params.get("from")
        to_param = self.request.query_params.get("to")
        if status_filter:
            qs = qs.filter(status=status_filter)
        if from_param:
            qs = qs.filter(starts_at__gte=from_param)
        if to_param:
            qs = qs.filter(starts_at__lte=to_param)
        return qs

    def perform_create(self, serializer):
        provider = get_provider_profile(self.request.user)
        serializer.save(provider=provider, rule=None)

    def destroy(self, request, *args, **kwargs):
        slot = self.get_object()
        if slot.status == AvailabilityProvider.Status.BOOKED:
            return Response(
                {"detail": "Cannot delete a booked slot."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)

    @provider_schema(
        summary="Block or reopen a slot", request=AvailabilitySlotBlockSerializer
    )
    @action(detail=True, methods=["post"], url_path="status")
    def set_status(self, request, pk=None):
        slot = self.get_object()
        if slot.status == AvailabilityProvider.Status.BOOKED:
            return Response(
                {"detail": "Cannot change status of a booked slot."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = AvailabilitySlotBlockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        slot.status = serializer.validated_data["status"]
        slot.save(update_fields=["status", "updated_at"])
        return Response(AvailabilitySlotSerializer(slot).data)


@extend_schema_view(
    list=provider_schema(summary="List bookings for my provider account"),
    retrieve=provider_schema(summary="Retrieve booking with customer domicile"),
)
class ProviderBookingViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated, IsProvider]
    serializer_class = BookingProviderSerializer

    def get_queryset(self):
        provider = get_provider_profile(self.request.user)
        return FactBooking.objects.filter(provider=provider).select_related(
            "customer",
            "service",
            "visit_location",
        )

    @provider_schema(summary="Confirm a pending booking")
    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        booking = self.get_object()
        try:
            transition_booking(booking, FactBooking.Status.CONFIRMED)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(BookingProviderSerializer(booking).data)

    @provider_schema(summary="Decline a pending booking")
    @action(detail=True, methods=["post"])
    def decline(self, request, pk=None):
        booking = self.get_object()
        try:
            transition_booking(booking, FactBooking.Status.DECLINED)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(BookingProviderSerializer(booking).data)

    @provider_schema(summary="Mark a confirmed booking as completed")
    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        booking = self.get_object()
        try:
            transition_booking(booking, FactBooking.Status.COMPLETED)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(BookingProviderSerializer(booking).data)

    @provider_schema(
        summary="Review customer after completed visit", request=ReviewCreateSerializer
    )
    @action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        booking = self.get_object()
        if hasattr(booking, "provider_review"):
            return Response(
                {"detail": "Review already submitted."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = ProviderReview.objects.create(
            reviewer=request.user,
            customer=booking.customer,
            booking=booking,
            rating=serializer.validated_data["rating"],
            comment=serializer.validated_data.get("comment", ""),
        )
        return Response(
            BookingProviderReviewSerializer(review).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    list=provider_schema(summary="List invoices for my provider account"),
    retrieve=provider_schema(summary="Retrieve an invoice"),
)
class ProviderInvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated, IsProvider]
    serializer_class = InvoiceSerializer

    def get_queryset(self):
        provider = get_provider_profile(self.request.user)
        return Invoice.objects.filter(provider=provider).select_related("booking")


@extend_schema_view(
    list=customer_schema(summary="List my availability windows"),
    create=customer_schema(summary="Add when I am available for a visit"),
    retrieve=customer_schema(summary="Retrieve an availability window"),
    destroy=customer_schema(summary="Remove an availability window"),
)
class CustomerAvailabilityViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsCustomer]
    serializer_class = CustomerAvailabilitySerializer
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):
        return AvailabilityCustomer.objects.filter(customer=self.request.user)

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)


@extend_schema_view(
    list=customer_schema(summary="List my bookings"),
    create=customer_schema(summary="Book a provider slot for a home visit"),
    retrieve=customer_schema(summary="Retrieve my booking"),
)
class CustomerBookingViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsCustomer]
    http_method_names = ["get", "post", "head", "options"]

    def get_serializer_class(self):
        if self.action == "create":
            return BookingCreateSerializer
        return BookingCustomerSerializer

    def get_queryset(self):
        return FactBooking.objects.filter(customer=self.request.user).select_related(
            "provider",
            "service",
            "visit_location",
        )

    def create(self, request, *args, **kwargs):
        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        customer_availability = data.get("customer_availability")
        if (
            customer_availability
            and customer_availability.customer_id != request.user.id
        ):
            return Response(
                {"detail": "Customer availability window does not belong to you."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            booking = create_booking(
                customer=request.user,
                provider=data["provider"],
                service=data["service"],
                provider_availability=data["provider_availability"],
                customer_availability=customer_availability,
                notes=data.get("notes", ""),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            BookingCustomerSerializer(booking).data,
            status=status.HTTP_201_CREATED,
        )

    @customer_schema(summary="Cancel my booking")
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        try:
            cancel_booking(booking)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(BookingCustomerSerializer(booking).data)

    @customer_schema(
        summary="Review provider after completed visit", request=ReviewCreateSerializer
    )
    @action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        booking = self.get_object()
        if hasattr(booking, "user_review"):
            return Response(
                {"detail": "Review already submitted."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = UserReview.objects.create(
            reviewer=request.user,
            provider=booking.provider,
            booking=booking,
            rating=serializer.validated_data["rating"],
            comment=serializer.validated_data.get("comment", ""),
        )
        return Response(
            BookingUserReviewSerializer(review).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    list=customer_schema(summary="List my invoices"),
    retrieve=customer_schema(summary="Retrieve an invoice"),
)
class CustomerInvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated, IsCustomer]
    serializer_class = InvoiceSerializer

    def get_queryset(self):
        return Invoice.objects.filter(customer=self.request.user).select_related(
            "booking"
        )

    @customer_schema(summary="Pay an invoice (stub)", request=PayInvoiceSerializer)
    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        invoice = self.get_object()
        serializer = PayInvoiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            payment = pay_invoice(
                invoice,
                payment_method=serializer.validated_data["payment_method"],
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {
                "invoice": InvoiceSerializer(invoice).data,
                "payment": PaymentSerializer(payment).data,
            }
        )


@extend_schema_view(
    list=marketplace_schema(summary="Discover active providers"),
    retrieve=marketplace_schema(summary="Provider public profile"),
)
class MarketplaceProviderViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = MarketplaceProviderSerializer

    def get_queryset(self):
        qs = (
            ProviderProfile.objects.filter(is_active=True)
            .select_related("service_area", "user")
            .prefetch_related("user__languages", "service_links__service")
        )
        service = self.request.query_params.get("service")
        language = self.request.query_params.get("language")
        if service:
            qs = qs.filter(service_links__service__slug=service)
        if language:
            qs = qs.filter(user__languages__code=language)
        return qs.distinct()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        lat = request.query_params.get("lat")
        lng = request.query_params.get("lng")
        page = self.paginate_queryset(queryset)
        items = page if page is not None else list(queryset)
        distance_map = {}
        if lat and lng:
            for provider in items:
                if location_has_coordinates(provider.service_area):
                    distance_map[provider.pk] = haversine_km(
                        lat,
                        lng,
                        provider.service_area.latitude,
                        provider.service_area.longitude,
                    )
            if distance_map:
                items = [
                    p
                    for p in items
                    if p.pk not in distance_map
                    or p.travel_radius_km is None
                    or distance_map[p.pk] <= p.travel_radius_km
                ]
        serializer = self.get_serializer(
            items,
            many=True,
            context={
                **self.get_serializer_context(),
                "distance_map": distance_map,
            },
        )
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        lat = request.query_params.get("lat")
        lng = request.query_params.get("lng")
        distance_map = {}
        if lat and lng and location_has_coordinates(instance.service_area):
            distance_map[instance.pk] = haversine_km(
                lat,
                lng,
                instance.service_area.latitude,
                instance.service_area.longitude,
            )
        serializer = self.get_serializer(
            instance,
            context={**self.get_serializer_context(), "distance_map": distance_map},
        )
        return Response(serializer.data)

    @marketplace_schema(summary="Open slots for a provider")
    @action(detail=True, methods=["get"])
    def slots(self, request, pk=None):
        provider = self.get_object()
        qs = AvailabilityProvider.objects.filter(
            provider=provider,
            status=AvailabilityProvider.Status.OPEN,
        ).select_related("service")
        from_param = request.query_params.get("from")
        to_param = request.query_params.get("to")
        service = request.query_params.get("service")
        if from_param:
            qs = qs.filter(starts_at__gte=from_param)
        if to_param:
            qs = qs.filter(starts_at__lte=to_param)
        if service:
            qs = qs.filter(service__slug=service)
        return Response(MarketplaceSlotSerializer(qs, many=True).data)


@customer_schema(summary="List my payments")
class CustomerPaymentListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsCustomer]
    serializer_class = PaymentSerializer

    def get_queryset(self):
        return FactPayment.objects.filter(
            booking__customer=self.request.user
        ).select_related("invoice", "booking")
