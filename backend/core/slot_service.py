from datetime import datetime, timedelta

from django.utils import timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .models import AvailabilityProvider, AvailabilityRule


def generate_provider_slots(provider, weeks: int = 4) -> list[AvailabilityProvider]:
    rules = AvailabilityRule.objects.filter(provider=provider, is_active=True)
    if not rules.exists():
        return []

    now = timezone.now()
    end_date = (now + timedelta(weeks=weeks)).date()
    day = now.date()
    created: list[AvailabilityProvider] = []

    while day <= end_date:
        for rule in rules:
            if day.weekday() != rule.weekday:
                continue
            if rule.valid_from and day < rule.valid_from:
                continue
            if rule.valid_until and day > rule.valid_until:
                continue

            try:
                tz = ZoneInfo(rule.timezone)
            except ZoneInfoNotFoundError:
                tz = ZoneInfo("UTC")

            start_naive = datetime.combine(day, rule.start_time)
            end_naive = datetime.combine(day, rule.end_time)
            starts_at = timezone.make_aware(start_naive, tz).astimezone(timezone.utc)
            ends_at = timezone.make_aware(end_naive, tz).astimezone(timezone.utc)

            if ends_at <= now:
                continue

            exists = AvailabilityProvider.objects.filter(
                provider=provider,
                rule=rule,
                starts_at=starts_at,
                ends_at=ends_at,
            ).exists()
            if exists:
                continue

            slot = AvailabilityProvider.objects.create(
                provider=provider,
                rule=rule,
                starts_at=starts_at,
                ends_at=ends_at,
                status=AvailabilityProvider.Status.OPEN,
            )
            created.append(slot)

        day += timedelta(days=1)

    return created
