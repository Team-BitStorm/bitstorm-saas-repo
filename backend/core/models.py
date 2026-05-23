from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

User = settings.AUTH_USER_MODEL

RATING_VALIDATORS = [
    MinValueValidator(1),
    MaxValueValidator(10),
]


class GeoLocation(models.Model):
    label = models.CharField(max_length=128, blank=True)
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=128, blank=True)
    region = models.CharField(max_length=128, blank=True)
    postal_code = models.CharField(max_length=32, blank=True)
    country = models.CharField(max_length=64, blank=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    owner_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="owned_locations",
        help_text="Set for private domicile rows; scopes address visibility.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "geo location"
        verbose_name_plural = "geo locations"

    def __str__(self) -> str:
        parts = [self.label, self.city, self.country]
        return ", ".join(p for p in parts if p) or f"Location #{self.pk}"


class Language(models.Model):
    code = models.CharField(max_length=8, unique=True)
    name = models.CharField(max_length=64)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    avatar_url = models.URLField(blank=True)
    bio = models.TextField(blank=True)
    home_location = models.ForeignKey(
        GeoLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_profiles",
    )

    def __str__(self) -> str:
        return f"Profile for {self.user.email}"


class ProviderProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="provider_profile",
    )
    display_name = models.CharField(max_length=128)
    bio = models.TextField(blank=True)
    service_area = models.ForeignKey(
        GeoLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="provider_profiles",
    )
    travel_radius_km = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Maximum travel distance from service area for home visits.",
    )
    is_active = models.BooleanField(default=True)

    def clean(self) -> None:
        super().clean()
        if self.user_id and self.user.role != self.user.Role.PROVIDER:
            raise ValidationError(
                {"user": "Provider profile requires a user with role 'provider'."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.display_name or self.user.get_full_name() or self.user.email


class Service(models.Model):
    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128, unique=True, blank=True)
    description = models.TextField(blank=True)
    min_price = models.DecimalField(max_digits=10, decimal_places=2)
    max_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def clean(self) -> None:
        super().clean()
        if self.min_price is not None and self.min_price < 0:
            raise ValidationError({"min_price": "Minimum price cannot be negative."})
        if self.max_price is not None and self.max_price < 0:
            raise ValidationError({"max_price": "Maximum price cannot be negative."})
        if (
            self.min_price is not None
            and self.max_price is not None
            and self.min_price > self.max_price
        ):
            raise ValidationError(
                {
                    "max_price": "Maximum price must be greater than or equal to minimum price."
                }
            )

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "service"
            slug = base_slug
            counter = 1
            while Service.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class ServiceProvider(models.Model):
    provider = models.ForeignKey(
        ProviderProfile,
        on_delete=models.CASCADE,
        related_name="service_links",
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="provider_links",
    )
    provider_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Typical visit duration for this provider and service.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("provider", "service")
        verbose_name = "service provider"
        verbose_name_plural = "service providers"

    def clean(self) -> None:
        super().clean()
        if self.provider_price is not None and self.provider_price < 0:
            raise ValidationError(
                {"provider_price": "Provider price cannot be negative."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.provider} — {self.service}"


class UserReview(models.Model):
    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reviews_given",
    )
    provider = models.ForeignKey(
        ProviderProfile,
        on_delete=models.CASCADE,
        related_name="reviews_received",
    )
    booking = models.OneToOneField(
        "FactBooking",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="user_review",
    )
    rating = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "user review"
        verbose_name_plural = "user reviews"

    def clean(self) -> None:
        super().clean()
        if self.reviewer_id and self.reviewer.role != self.reviewer.Role.CUSTOMER:
            raise ValidationError(
                {"reviewer": "Only customers can submit user reviews."}
            )
        if self.booking_id:
            if self.booking.customer_id != self.reviewer_id:
                raise ValidationError(
                    {"booking": "Review customer must match the booking customer."}
                )
            if self.booking.provider_id != self.provider_id:
                raise ValidationError(
                    {"booking": "Review provider must match the booking provider."}
                )
            if self.booking.status != "completed":
                raise ValidationError(
                    {"booking": "Reviews are allowed only for completed bookings."}
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Review by {self.reviewer.email} for {self.provider}"


class ProviderReview(models.Model):
    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="provider_reviews_given",
    )
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="provider_reviews_received",
    )
    booking = models.OneToOneField(
        "FactBooking",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="provider_review",
    )
    rating = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "provider review"
        verbose_name_plural = "provider reviews"

    def clean(self) -> None:
        super().clean()
        if self.reviewer_id and self.reviewer.role != self.reviewer.Role.PROVIDER:
            raise ValidationError(
                {"reviewer": "Only providers can submit provider reviews."}
            )
        if self.customer_id and self.customer.role != self.customer.Role.CUSTOMER:
            raise ValidationError(
                {"customer": "Provider reviews must target a customer."}
            )
        if (
            self.reviewer_id
            and self.customer_id
            and self.reviewer_id == self.customer_id
        ):
            raise ValidationError("A user cannot review themselves.")
        if self.booking_id:
            if self.booking.customer_id != self.customer_id:
                raise ValidationError(
                    {"booking": "Review customer must match the booking customer."}
                )
            if self.booking.provider.user_id != self.reviewer_id:
                raise ValidationError(
                    {"booking": "Review provider must match the booking provider."}
                )
            if self.booking.status != "completed":
                raise ValidationError(
                    {"booking": "Reviews are allowed only for completed bookings."}
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Review by {self.reviewer.email} for {self.customer.email}"


class AvailabilityRule(models.Model):
    class Weekday(models.IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thursday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"
        SUNDAY = 6, "Sunday"

    provider = models.ForeignKey(
        ProviderProfile,
        on_delete=models.CASCADE,
        related_name="availability_rules",
    )
    weekday = models.PositiveSmallIntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    timezone = models.CharField(max_length=64, default="UTC")
    is_active = models.BooleanField(default=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "availability_rule"
        ordering = ["provider", "weekday", "start_time"]
        verbose_name = "availability rule"
        verbose_name_plural = "availability rules"

    def clean(self) -> None:
        super().clean()
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({"end_time": "End time must be after start time."})
        if self.valid_from and self.valid_until and self.valid_from > self.valid_until:
            raise ValidationError(
                {"valid_until": "Valid until must be on or after valid from."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.provider} — {self.get_weekday_display()} {self.start_time}-{self.end_time}"


class AvailabilityProvider(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        BOOKED = "booked", "Booked"
        BLOCKED = "blocked", "Blocked"
        CANCELLED = "cancelled", "Cancelled"

    provider = models.ForeignKey(
        ProviderProfile,
        on_delete=models.CASCADE,
        related_name="availability_slots",
    )
    rule = models.ForeignKey(
        AvailabilityRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_slots",
        help_text="Null when the slot was added manually outside a recurring rule.",
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="provider_availability_slots",
    )
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.OPEN,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "availability_providers"
        ordering = ["starts_at"]
        indexes = [
            models.Index(fields=["provider", "starts_at"]),
            models.Index(fields=["status", "starts_at"]),
        ]
        verbose_name = "provider availability slot"
        verbose_name_plural = "provider availability slots"

    def clean(self) -> None:
        super().clean()
        if self.starts_at and self.ends_at and self.starts_at >= self.ends_at:
            raise ValidationError({"ends_at": "End must be after start."})
        if self.rule_id and self.rule.provider_id != self.provider_id:
            raise ValidationError(
                {"rule": "Availability rule must belong to the same provider."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.provider} — {self.starts_at} ({self.status})"


class AvailabilityCustomer(models.Model):
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="availability_windows",
    )
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "availability_customers"
        ordering = ["starts_at"]
        indexes = [
            models.Index(fields=["customer", "starts_at"]),
        ]
        verbose_name = "customer availability window"
        verbose_name_plural = "customer availability windows"

    def clean(self) -> None:
        super().clean()
        if self.customer_id and self.customer.role != self.customer.Role.CUSTOMER:
            raise ValidationError(
                {"customer": "Only customers can define customer availability windows."}
            )
        if self.starts_at and self.ends_at and self.starts_at >= self.ends_at:
            raise ValidationError({"ends_at": "End must be after start."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.customer.email} — {self.starts_at}"


class FactBooking(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        DECLINED = "declined", "Declined"

    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="bookings_as_customer",
    )
    provider = models.ForeignKey(
        ProviderProfile,
        on_delete=models.CASCADE,
        related_name="bookings_as_provider",
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    service_link = models.ForeignKey(
        ServiceProvider,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
        help_text="Provider-service offering used for pricing at booking time.",
    )
    provider_availability = models.ForeignKey(
        AvailabilityProvider,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
    )
    customer_availability = models.ForeignKey(
        AvailabilityCustomer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
    )
    visit_location = models.ForeignKey(
        GeoLocation,
        on_delete=models.PROTECT,
        related_name="bookings",
        help_text="Customer domicile for this visit; visible only via booking scope.",
    )
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Booked service price snapshot.",
    )
    price_min = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    price_max = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    travel_km = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    travel_time_minutes = models.PositiveIntegerField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "fact_bookings"
        ordering = ["-starts_at"]
        indexes = [
            models.Index(fields=["customer", "status"]),
            models.Index(fields=["provider", "status"]),
            models.Index(fields=["starts_at"]),
        ]
        verbose_name = "booking"
        verbose_name_plural = "bookings"

    def clean(self) -> None:
        super().clean()
        if self.customer_id and self.customer.role != self.customer.Role.CUSTOMER:
            raise ValidationError({"customer": "Bookings require a customer account."})
        if self.starts_at and self.ends_at and self.starts_at >= self.ends_at:
            raise ValidationError({"ends_at": "End must be after start."})
        if self.price_min is not None and self.price_max is not None:
            if self.price_min > self.price_max:
                raise ValidationError(
                    {"price_max": "Maximum price must be >= minimum price."}
                )
        if self.provider_availability_id:
            slot = self.provider_availability
            if slot.provider_id != self.provider_id:
                raise ValidationError(
                    {
                        "provider_availability": "Slot must belong to the booking provider."
                    }
                )
            conflicting = slot.bookings.all()
            if self.pk:
                conflicting = conflicting.exclude(pk=self.pk)
            if conflicting.exists():
                raise ValidationError(
                    {"provider_availability": "This provider slot is already booked."}
                )
            is_existing_on_slot = self.pk and slot.bookings.filter(pk=self.pk).exists()
            if (
                slot.status != AvailabilityProvider.Status.OPEN
                and not is_existing_on_slot
            ):
                raise ValidationError(
                    {"provider_availability": "Provider slot must be open to book."}
                )
        if self.customer_availability_id:
            if self.customer_availability.customer_id != self.customer_id:
                raise ValidationError(
                    {
                        "customer_availability": "Window must belong to the booking customer."
                    }
                )
        if self.service_link_id:
            if self.service_link.provider_id != self.provider_id:
                raise ValidationError(
                    {
                        "service_link": "Service link must belong to the booking provider."
                    }
                )
            if self.service_link.service_id != self.service_id:
                raise ValidationError(
                    {"service_link": "Service link must match the booked service."}
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.status == self.Status.CONFIRMED and self.confirmed_at is None:
            self.confirmed_at = timezone.now()
        if self.status == self.Status.COMPLETED and self.completed_at is None:
            self.completed_at = timezone.now()
        if self.status == self.Status.CANCELLED and self.cancelled_at is None:
            self.cancelled_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Booking #{self.pk} — {self.customer.email} / {self.provider}"


class Invoice(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ISSUED = "issued", "Issued"
        PAID = "paid", "Paid"
        VOID = "void", "Void"

    booking = models.OneToOneField(
        FactBooking,
        on_delete=models.CASCADE,
        related_name="invoice",
    )
    customer = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="invoices_as_customer",
    )
    provider = models.ForeignKey(
        ProviderProfile,
        on_delete=models.PROTECT,
        related_name="invoices_as_provider",
    )
    invoice_number = models.CharField(max_length=64, unique=True)
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    tax = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    currency = models.CharField(max_length=3, default="RON")
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    issued_at = models.DateTimeField(null=True, blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "invoices"
        ordering = ["-created_at"]
        verbose_name = "invoice"
        verbose_name_plural = "invoices"

    def clean(self) -> None:
        super().clean()
        if self.booking_id:
            if self.customer_id and self.booking.customer_id != self.customer_id:
                raise ValidationError(
                    {"customer": "Invoice customer must match the booking customer."}
                )
            if self.provider_id and self.booking.provider_id != self.provider_id:
                raise ValidationError(
                    {"provider": "Invoice provider must match the booking provider."}
                )
        if (
            self.total is not None
            and self.subtotal is not None
            and self.tax is not None
        ):
            expected = self.subtotal + self.tax
            if self.total != expected:
                raise ValidationError({"total": "Total must equal subtotal plus tax."})

    def save(self, *args, **kwargs):
        if self.status == self.Status.ISSUED and self.issued_at is None:
            self.issued_at = timezone.now()
        if self.status == self.Status.PAID and self.paid_at is None:
            self.paid_at = timezone.now()
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.invoice_number


class FactPayment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    class Method(models.TextChoices):
        CARD = "card", "Card"
        CASH = "cash", "Cash"
        TRANSFER = "transfer", "Bank transfer"

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )
    booking = models.ForeignKey(
        FactBooking,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    currency = models.CharField(max_length=3, default="RON")
    payment_method = models.CharField(
        max_length=16,
        choices=Method.choices,
        default=Method.CARD,
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    external_reference = models.CharField(max_length=128, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "fact_payments"
        ordering = ["-created_at"]
        verbose_name = "payment"
        verbose_name_plural = "payments"

    def clean(self) -> None:
        super().clean()
        if self.invoice_id and self.booking_id:
            if self.invoice.booking_id != self.booking_id:
                raise ValidationError(
                    {"booking": "Payment booking must match the invoice booking."}
                )

    def save(self, *args, **kwargs):
        if self.status == self.Status.COMPLETED and self.paid_at is None:
            self.paid_at = timezone.now()
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Payment #{self.pk} — {self.amount} {self.currency} ({self.status})"
