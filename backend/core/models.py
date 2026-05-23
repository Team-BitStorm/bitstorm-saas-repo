from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
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
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("provider", "service")
        verbose_name = "service provider"
        verbose_name_plural = "service providers"

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
    rating = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("reviewer", "provider")
        verbose_name = "user review"
        verbose_name_plural = "user reviews"

    def clean(self) -> None:
        super().clean()
        if self.reviewer_id and self.reviewer.role != self.reviewer.Role.CUSTOMER:
            raise ValidationError(
                {"reviewer": "Only customers can submit user reviews."}
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
    rating = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("reviewer", "customer")
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

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Review by {self.reviewer.email} for {self.customer.email}"
