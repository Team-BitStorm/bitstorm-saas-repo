from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from encrypted_model_fields.fields import EncryptedCharField


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = "customer", "Customer"
        PROVIDER = "provider", "Provider"

    username = None
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=32, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    social_security_number = EncryptedCharField(max_length=32, blank=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
    )
    totp_confirmed = models.BooleanField(default=False)
    totp_secret = models.TextField(blank=True, default="")
    sms_2fa_enabled = models.BooleanField(default=False)
    cnp_lookup_hash = models.CharField(max_length=64, blank=True, default="")
    languages = models.ManyToManyField(
        "core.Language",
        blank=True,
        related_name="users",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    def __str__(self) -> str:
        return self.email
