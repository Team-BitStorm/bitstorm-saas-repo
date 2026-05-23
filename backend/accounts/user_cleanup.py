"""Remove dependent rows before user delete (ORM admin, shell, API)."""

from django.db import transaction


@transaction.atomic
def cleanup_user_before_delete(user) -> None:
    from rest_framework_simplejwt.token_blacklist.models import (
        BlacklistedToken,
        OutstandingToken,
    )

    from core.models import (
        AvailabilityCustomer,
        FactBooking,
        FactPayment,
        GeoLocation,
        Invoice,
        ProviderReview,
        UserReview,
    )

    # Blacklisted rows must go before outstanding tokens when DB FKs are RESTRICT.
    outstanding_ids = OutstandingToken.objects.filter(user=user).values_list(
        "pk", flat=True
    )
    BlacklistedToken.objects.filter(token_id__in=outstanding_ids).delete()
    OutstandingToken.objects.filter(user=user).delete()

    FactPayment.objects.filter(booking__customer=user).delete()
    FactPayment.objects.filter(invoice__customer=user).delete()

    Invoice.objects.filter(customer=user).delete()

    provider_profile = getattr(user, "provider_profile", None)
    if provider_profile is not None:
        FactPayment.objects.filter(booking__provider=provider_profile).delete()
        Invoice.objects.filter(provider=provider_profile).delete()
        FactBooking.objects.filter(provider=provider_profile).delete()

    UserReview.objects.filter(reviewer=user).delete()
    ProviderReview.objects.filter(reviewer=user).delete()
    ProviderReview.objects.filter(customer=user).delete()
    AvailabilityCustomer.objects.filter(customer=user).delete()
    FactBooking.objects.filter(customer=user).delete()
    GeoLocation.objects.filter(owner_user=user).delete()
