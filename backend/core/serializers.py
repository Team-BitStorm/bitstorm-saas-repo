from django.contrib.auth import get_user_model
from rest_framework import serializers

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

User = get_user_model()


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ("id", "code", "name")


class GeoLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeoLocation
        fields = (
            "id",
            "label",
            "address_line1",
            "address_line2",
            "city",
            "region",
            "postal_code",
            "country",
            "latitude",
            "longitude",
            "created_at",
        )


class UserPublicSerializer(serializers.ModelSerializer):
    languages = LanguageSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "languages",
        )


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(read_only=True)
    home_location = GeoLocationSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ("id", "user", "avatar_url", "bio", "home_location")


class ProviderProfileSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(read_only=True)
    service_area = GeoLocationSerializer(read_only=True)

    class Meta:
        model = ProviderProfile
        fields = (
            "id",
            "user",
            "display_name",
            "bio",
            "service_area",
            "travel_radius_km",
            "is_active",
        )


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "min_price",
            "max_price",
            "is_active",
            "created_at",
            "updated_at",
        )


class ServiceProviderSerializer(serializers.ModelSerializer):
    provider = ProviderProfileSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)

    class Meta:
        model = ServiceProvider
        fields = (
            "id",
            "provider",
            "service",
            "provider_price",
            "duration_minutes",
            "created_at",
            "updated_at",
        )


class UserReviewSerializer(serializers.ModelSerializer):
    reviewer = UserPublicSerializer(read_only=True)
    provider = ProviderProfileSerializer(read_only=True)

    class Meta:
        model = UserReview
        fields = (
            "id",
            "reviewer",
            "provider",
            "rating",
            "comment",
            "created_at",
            "updated_at",
        )


class ProviderReviewSerializer(serializers.ModelSerializer):
    reviewer = UserPublicSerializer(read_only=True)
    customer = UserPublicSerializer(read_only=True)

    class Meta:
        model = ProviderReview
        fields = (
            "id",
            "reviewer",
            "customer",
            "rating",
            "comment",
            "created_at",
            "updated_at",
        )
