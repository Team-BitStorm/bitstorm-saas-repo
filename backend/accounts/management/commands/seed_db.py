"""
Populate the database with demo data for development / hackathon demos.

Usage (from backend/):
    uv run python manage.py migrate
    uv run python manage.py seed_db

For bulk CSV seed data (20 demo users from backend/db/), use load_seed_csv instead.

Re-run safely: uses update_or_create on emails. Use --clear to wipe seeded rows first.
"""

from __future__ import annotations

from datetime import date, timedelta

from django.contrib.admin.models import ADDITION, CHANGE, LogEntry
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.settings import api_settings as jwt_settings
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User

DEMO_PASSWORD = "CarePath2026!"

SEED_GROUP_NAMES = ("Customers", "Providers", "Staff")

SEED_USERS: tuple[dict, ...] = (
    {
        "email": "admin@carepath.test",
        "first_name": "CarePath",
        "last_name": "Admin",
        "phone_number": "+1 555 0000",
        "birth_date": date(1985, 1, 1),
        "role": User.Role.PROVIDER,
        "is_staff": True,
        "is_superuser": True,
        "groups": ("Staff",),
        "direct_permissions": (),
        "seed_session": True,
        "seed_tokens": False,
    },
    {
        "email": "margaret@carepath.test",
        "first_name": "Margaret",
        "last_name": "Hollis",
        "phone_number": "+1 555 0100",
        "birth_date": date(1942, 3, 14),
        "social_security_number": "000-00-0001",
        "role": User.Role.CUSTOMER,
        "is_staff": False,
        "is_superuser": False,
        "groups": ("Customers",),
        "direct_permissions": ("view_user",),
        "seed_session": False,
        "seed_tokens": True,
        "blacklist_refresh": True,
    },
    {
        "email": "sarah@carepath.test",
        "first_name": "Sarah",
        "last_name": "Hollis",
        "phone_number": "+1 555 0101",
        "birth_date": date(1975, 6, 20),
        "role": User.Role.PROVIDER,
        "is_staff": False,
        "is_superuser": False,
        "groups": ("Providers",),
        "direct_permissions": (),
        "seed_session": False,
        "seed_tokens": True,
        "blacklist_refresh": False,
    },
    {
        "email": "daniel@carepath.test",
        "first_name": "Daniel",
        "last_name": "Nurse",
        "phone_number": "+1 555 0144",
        "birth_date": date(1988, 11, 2),
        "role": User.Role.PROVIDER,
        "is_staff": False,
        "is_superuser": False,
        "groups": ("Providers",),
        "direct_permissions": (),
        "seed_session": False,
        "seed_tokens": False,
        "blacklist_refresh": False,
    },
    {
        "email": "andrei@carepath.test",
        "first_name": "Andrei",
        "last_name": "Codreanu",
        "phone_number": "+1 555 0200",
        "birth_date": date(1990, 4, 12),
        "role": User.Role.CUSTOMER,
        "is_staff": False,
        "is_superuser": False,
        "groups": ("Customers",),
        "direct_permissions": (),
        "seed_session": False,
        "seed_tokens": False,
        "blacklist_refresh": False,
    },
)


class Command(BaseCommand):
    help = "Seed demo users, auth groups, JWT tokens, sessions, and admin log entries."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete previously seeded rows before inserting demo data.",
        )
        parser.add_argument(
            "--password",
            default=DEMO_PASSWORD,
            help=f"Password for all demo users (default: {DEMO_PASSWORD}).",
        )

    def handle(self, *args, **options):
        password: str = options["password"]
        if options["clear"]:
            self._clear_seeded_data()

        with transaction.atomic():
            groups = self._ensure_groups()
            users = self._ensure_users(password, groups)
            self._seed_group_permissions(groups)
            self._assign_groups_and_permissions(users, groups)
            token_stats = self._seed_jwt_tokens(users, password)
            session_count = self._seed_admin_session(users["admin@carepath.test"])
            log_count = self._seed_admin_log(users)

        self.stdout.write(self.style.SUCCESS("Database seeded successfully."))
        self.stdout.write(f"  Users: {len(users)}")
        self.stdout.write(f"  Groups: {len(groups)}")
        self.stdout.write(
            f"  JWT outstanding / blacklisted: {token_stats['outstanding']} / {token_stats['blacklisted']}"
        )
        self.stdout.write(f"  Django sessions: {session_count}")
        self.stdout.write(f"  Admin log entries: {log_count}")
        self.stdout.write("")
        self.stdout.write(self.style.WARNING(f"Demo password for all users: {password}"))
        self.stdout.write("Login examples:")
        self.stdout.write("  - API: POST /api/auth/login/  email=margaret@carepath.test")
        self.stdout.write("  - Admin: http://127.0.0.1:8000/admin/  admin@carepath.test")

    def _clear_seeded_data(self) -> None:
        self.stdout.write("Clearing seeded data…")
        emails = [row["email"] for row in SEED_USERS]

        BlacklistedToken.objects.all().delete()
        OutstandingToken.objects.filter(user__email__in=emails).delete()
        Session.objects.all().delete()
        LogEntry.objects.filter(user__email__in=emails).delete()

        User.objects.filter(email__in=emails).delete()
        Group.objects.filter(name__in=SEED_GROUP_NAMES).delete()

    def _ensure_groups(self) -> dict[str, Group]:
        groups: dict[str, Group] = {}
        for name in SEED_GROUP_NAMES:
            group, _ = Group.objects.get_or_create(name=name)
            groups[name] = group
        return groups

    def _user_permissions(self) -> dict[str, Permission]:
        content_type = ContentType.objects.get_for_model(User)
        perms = Permission.objects.filter(content_type=content_type)
        return {perm.codename: perm for perm in perms}

    def _seed_group_permissions(self, groups: dict[str, Group]) -> None:
        perms = self._user_permissions()
        view = perms.get("view_user")
        change = perms.get("change_user")
        add = perms.get("add_user")
        delete = perms.get("delete_user")

        if view:
            groups["Customers"].permissions.set([view])
        if view and change:
            groups["Providers"].permissions.set([view, change])
        if view and change and add and delete:
            groups["Staff"].permissions.set([view, change, add, delete])

    def _ensure_users(self, password: str, groups: dict[str, Group]) -> dict[str, User]:
        users: dict[str, User] = {}
        for spec in SEED_USERS:
            email = spec["email"]
            user, created = User.objects.update_or_create(
                email=email,
                defaults={
                    "first_name": spec["first_name"],
                    "last_name": spec["last_name"],
                    "phone_number": spec.get("phone_number", ""),
                    "birth_date": spec.get("birth_date"),
                    "social_security_number": spec.get("social_security_number", ""),
                    "role": spec["role"],
                    "is_staff": spec["is_staff"],
                    "is_superuser": spec["is_superuser"],
                    "is_active": True,
                },
            )
            user.set_password(password)
            user.save(update_fields=["password"])
            users[email] = user
            action = "Created" if created else "Updated"
            self.stdout.write(f"  {action} user {email}")
        return users

    def _assign_groups_and_permissions(
        self,
        users: dict[str, User],
        groups: dict[str, Group],
    ) -> None:
        perms = self._user_permissions()
        for spec in SEED_USERS:
            user = users[spec["email"]]
            user.groups.set([groups[name] for name in spec["groups"]])
            direct = [perms[codename] for codename in spec["direct_permissions"] if codename in perms]
            user.user_permissions.set(direct)

    def _seed_jwt_tokens(self, users: dict[str, User], password: str) -> dict[str, int]:
        outstanding = 0
        blacklisted = 0
        now = timezone.now()

        for spec in SEED_USERS:
            if not spec.get("seed_tokens"):
                continue

            user = users[spec["email"]]
            refresh = RefreshToken.for_user(user)
            jti = str(refresh[jwt_settings.JTI_CLAIM])
            expires_at = now + timedelta(seconds=int(refresh.lifetime.total_seconds()))

            token_row, created = OutstandingToken.objects.update_or_create(
                jti=jti,
                defaults={
                    "user": user,
                    "token": str(refresh),
                    "created_at": now,
                    "expires_at": expires_at,
                },
            )
            if created:
                outstanding += 1

            if spec.get("blacklist_refresh"):
                _, bl_created = BlacklistedToken.objects.get_or_create(
                    token=token_row,
                    defaults={"blacklisted_at": now},
                )
                if bl_created:
                    blacklisted += 1

        return {"outstanding": outstanding, "blacklisted": blacklisted}

    def _seed_admin_session(self, admin_user: User) -> int:
        store = SessionStore()
        store["_auth_user_id"] = str(admin_user.pk)
        store["_auth_user_backend"] = "django.contrib.auth.backends.ModelBackend"
        store.create()
        return 1

    def _seed_admin_log(self, users: dict[str, User]) -> int:
        admin = users["admin@carepath.test"]
        content_type = ContentType.objects.get_for_model(User)
        now = timezone.now()
        created = 0

        for email in ("margaret@carepath.test", "sarah@carepath.test"):
            target = users[email]
            LogEntry.objects.update_or_create(
                user=admin,
                content_type=content_type,
                object_id=str(target.pk),
                action_flag=ADDITION,
                defaults={
                    "object_repr": str(target),
                    "change_message": "Seeded demo user via seed_db.",
                    "action_time": now,
                },
            )
            created += 1

        LogEntry.objects.update_or_create(
            user=admin,
            content_type=content_type,
            object_id=str(users["margaret@carepath.test"].pk),
            action_flag=CHANGE,
            defaults={
                "object_repr": str(users["margaret@carepath.test"]),
                "change_message": "Updated patient profile (demo).",
                "action_time": now + timedelta(minutes=1),
            },
        )
        created += 1

        return created
