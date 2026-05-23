import uuid
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .geo_utils import (
    estimate_travel_time_minutes,
    haversine_km,
    location_has_coordinates,
)
from .models import (
    AvailabilityProvider,
    FactBooking,
    FactPayment,
    GeoLocation,
    Invoice,
    ProviderProfile,
    ServiceProvider,
)


def copy_geolocation(source: GeoLocation) -> GeoLocation:
    return GeoLocation.objects.create(
        label=source.label,
        address_line1=source.address_line1,
        address_line2=source.address_line2,
        city=source.city,
        region=source.region,
        postal_code=source.postal_code,
        country=source.country,
        latitude=source.latitude,
        longitude=source.longitude,
        owner_user=source.owner_user,
    )


def compute_travel_metrics(provider: ProviderProfile, visit_location: GeoLocation):
    service_area = provider.service_area
    if not location_has_coordinates(service_area) or not location_has_coordinates(
        visit_location
    ):
        return None, None
    distance = haversine_km(
        service_area.latitude,
        service_area.longitude,
        visit_location.latitude,
        visit_location.longitude,
    )
    return distance, estimate_travel_time_minutes(distance)


def customer_within_provider_radius(
    provider: ProviderProfile, visit_location: GeoLocation
) -> bool:
    if provider.travel_radius_km is None:
        return True
    distance, _ = compute_travel_metrics(provider, visit_location)
    if distance is None:
        return False
    return distance <= provider.travel_radius_km


@transaction.atomic
def create_booking(
    *,
    customer,
    provider: ProviderProfile,
    service,
    provider_availability: AvailabilityProvider,
    customer_availability=None,
    notes: str = "",
) -> FactBooking:
    service_link = ServiceProvider.objects.filter(
        provider=provider, service=service
    ).first()
    if service_link is None:
        raise ValueError("Provider does not offer this service.")

    if provider_availability.provider_id != provider.id:
        raise ValueError("Slot does not belong to this provider.")
    if provider_availability.status != AvailabilityProvider.Status.OPEN:
        raise ValueError("Provider slot is not open.")

    profile = getattr(customer, "profile", None)
    if profile is None or profile.home_location_id is None:
        raise ValueError("Customer home location is required before booking.")

    home = profile.home_location
    if not customer_within_provider_radius(provider, home):
        raise ValueError("Customer location is outside provider travel radius.")

    visit_snapshot = copy_geolocation(home)
    travel_km, travel_time = compute_travel_metrics(provider, visit_snapshot)

    price = service_link.provider_price or service.min_price
    duration = service_link.duration_minutes

    booking = FactBooking(
        customer=customer,
        provider=provider,
        service=service,
        service_link=service_link,
        provider_availability=provider_availability,
        customer_availability=customer_availability,
        visit_location=visit_snapshot,
        starts_at=provider_availability.starts_at,
        ends_at=provider_availability.ends_at,
        price=price,
        price_min=service.min_price,
        price_max=service.max_price,
        travel_km=travel_km,
        travel_time_minutes=travel_time,
        duration_minutes=duration,
        notes=notes,
        status=FactBooking.Status.PENDING,
    )
    booking.save()

    provider_availability.status = AvailabilityProvider.Status.BOOKED
    provider_availability.save(update_fields=["status", "updated_at"])

    return booking


@transaction.atomic
def cancel_booking(booking: FactBooking) -> FactBooking:
    if booking.status in (
        FactBooking.Status.COMPLETED,
        FactBooking.Status.CANCELLED,
        FactBooking.Status.DECLINED,
    ):
        raise ValueError(f"Cannot cancel booking in status '{booking.status}'.")
    booking.status = FactBooking.Status.CANCELLED
    booking.save()
    if booking.provider_availability_id:
        slot = booking.provider_availability
        slot.status = AvailabilityProvider.Status.OPEN
        slot.save(update_fields=["status", "updated_at"])
    return booking


@transaction.atomic
def transition_booking(booking: FactBooking, new_status: str) -> FactBooking:
    allowed = {
        FactBooking.Status.PENDING: {
            FactBooking.Status.CONFIRMED,
            FactBooking.Status.DECLINED,
            FactBooking.Status.CANCELLED,
        },
        FactBooking.Status.CONFIRMED: {
            FactBooking.Status.COMPLETED,
            FactBooking.Status.CANCELLED,
        },
    }
    current = booking.status
    if new_status not in allowed.get(current, set()):
        raise ValueError(f"Cannot transition from '{current}' to '{new_status}'.")

    booking.status = new_status
    booking.save()

    if new_status == FactBooking.Status.DECLINED:
        if booking.provider_availability_id:
            slot = booking.provider_availability
            slot.status = AvailabilityProvider.Status.OPEN
            slot.save(update_fields=["status", "updated_at"])
    elif new_status == FactBooking.Status.CONFIRMED:
        _ensure_draft_invoice(booking)
    elif new_status == FactBooking.Status.COMPLETED:
        _issue_invoice_if_needed(booking)

    return booking


def _ensure_draft_invoice(booking: FactBooking) -> Invoice:
    invoice, _ = Invoice.objects.get_or_create(
        booking=booking,
        defaults={
            "customer": booking.customer,
            "provider": booking.provider,
            "invoice_number": f"INV-{booking.pk}-{uuid.uuid4().hex[:8].upper()}",
            "subtotal": booking.price,
            "tax": Decimal("0"),
            "total": booking.price,
            "status": Invoice.Status.DRAFT,
        },
    )
    return invoice


def _issue_invoice_if_needed(booking: FactBooking) -> Invoice:
    invoice = _ensure_draft_invoice(booking)
    if invoice.status == Invoice.Status.DRAFT:
        invoice.status = Invoice.Status.ISSUED
        invoice.due_at = timezone.now() + timezone.timedelta(days=7)
        invoice.save()
    return invoice


@transaction.atomic
def pay_invoice(
    invoice: Invoice, payment_method: str = FactPayment.Method.CARD
) -> FactPayment:
    if invoice.status not in (Invoice.Status.ISSUED, Invoice.Status.DRAFT):
        raise ValueError("Invoice is not payable.")

    if invoice.status == Invoice.Status.DRAFT:
        invoice.status = Invoice.Status.ISSUED
        invoice.issued_at = timezone.now()
        invoice.save()

    payment = FactPayment.objects.create(
        invoice=invoice,
        booking=invoice.booking,
        amount=invoice.total,
        currency=invoice.currency,
        payment_method=payment_method,
        status=FactPayment.Status.COMPLETED,
        external_reference=f"stub-{uuid.uuid4().hex[:12]}",
    )
    invoice.status = Invoice.Status.PAID
    invoice.save()
    return payment
