"""
Load seed data from backend/db/**/*.csv into PostgreSQL.

Usage (from backend/):
    python scripts/build_seed_csvs.py
    python manage.py migrate
    python manage.py load_seed_csv --clear
"""

from __future__ import annotations

import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.conf import settings
from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from accounts.models import User

DEFAULT_PASSWORD = "CarePath2026!"

ACTION_FLAG_MAP = {
    "1": ADDITION,
    "2": CHANGE,
    "3": DELETION,
}

CLEAR_TABLES = (
    "token_blacklist_blacklistedtoken",
    "token_blacklist_outstandingtoken",
    "django_admin_log",
    "django_session",
    "fact_payments",
    "invoices",
    "fact_bookings",
    "core_providerreview",
    "core_userreview",
    "core_serviceprovider",
    "availability_providers",
    "availability_customers",
    "availability_rule",
    "core_service",
    "core_providerprofile",
    "core_userprofile",
    "accounts_user_languages",
    "accounts_user_user_permissions",
    "accounts_user_groups",
    "core_geolocation",
    "accounts_user",
    "core_language",
    "auth_group_permissions",
    "auth_group",
)

SEQUENCE_TABLES = (
    "accounts_user",
    "auth_group",
    "core_language",
    "core_geolocation",
    "core_userprofile",
    "core_providerprofile",
    "core_service",
    "core_serviceprovider",
    "core_userreview",
    "core_providerreview",
    "availability_rule",
    "availability_customers",
    "availability_providers",
    "fact_bookings",
    "fact_payments",
    "invoices",
    "django_admin_log",
    "token_blacklist_outstandingtoken",
    "token_blacklist_blacklistedtoken",
    "accounts_user_languages",
)


def _db_root() -> Path:
    return Path(settings.BASE_DIR) / "db"


def _csv_path(*parts: str) -> Path:
    path = _db_root().joinpath(*parts)
    if not path.is_file():
        raise CommandError(f"Missing seed file: {path}")
    return path


def _optional_csv_path(*parts: str) -> Path | None:
    path = _db_root().joinpath(*parts)
    return path if path.is_file() else None


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _parse_dt(value: str | None):
    if not value or not str(value).strip():
        return None
    parsed = parse_datetime(str(value).strip())
    if parsed is None:
        return None
    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed)
    return parsed


def _parse_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _clean(value: str | None):
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _parse_decimal(value: str | None):
    text = _clean(value)
    if text is None:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return Decimal("0")


def _parse_int(value: str | None):
    text = _clean(value)
    if text is None:
        return None
    return int(float(text))


class Command(BaseCommand):
    help = "Load seed CSV files from backend/db/ into the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete previously seeded rows before loading CSV data.",
        )
        parser.add_argument(
            "--password",
            default=DEFAULT_PASSWORD,
            help=f"Password applied to all loaded users (default: {DEFAULT_PASSWORD}).",
        )

    def handle(self, *args, **options):
        db_root = _db_root()
        if not db_root.is_dir():
            raise CommandError(f"Seed directory not found: {db_root}")

        password: str = options["password"]
        if options["clear"]:
            self._clear()

        stats: dict[str, int] = {}
        with transaction.atomic():
            stats["groups"] = len(self._load_groups())
            stats["languages"] = self._load_simple_table("core_language", "core", "core_language.csv")
            users = self._load_users(password)
            stats["users"] = len(users)
            stats["geolocations"] = self._load_simple_table(
                "core_geolocation", "core", "core_geolocation.csv"
            )
            stats["user_profiles"] = self._load_simple_table(
                "core_userprofile", "core", "core_userprofile.csv"
            )
            stats["provider_profiles"] = self._load_simple_table(
                "core_providerprofile", "core", "core_providerprofile.csv"
            )
            stats["services"] = self._load_simple_table("core_service", "core", "core_service.csv")
            stats["service_providers"] = self._load_simple_table(
                "core_serviceprovider", "core", "core_serviceprovider.csv"
            )
            self._load_user_groups(users, self._groups_cache)
            self._load_group_permissions(self._groups_cache)
            self._load_user_permissions(users)
            stats["user_languages"] = self._load_simple_table(
                "accounts_user_languages", "accounts", "accounts_user_languages.csv"
            )
            stats["availability_rules"] = self._load_simple_table(
                "availability_rule", "availability", "availability_rule.csv"
            )
            stats["availability_customers"] = self._load_simple_table(
                "availability_customers", "availability", "availability_customers.csv"
            )
            stats["availability_providers"] = self._load_simple_table(
                "availability_providers", "availability", "availability_providers.csv"
            )
            stats["bookings"] = self._load_simple_table("fact_bookings", "fact", "fact_bookings.csv")
            stats["invoices"] = self._load_simple_table("invoices", "fact", "invoices.csv")
            stats["payments"] = self._load_simple_table("fact_payments", "fact", "fact_payments.csv")
            stats["user_reviews"] = self._load_simple_table(
                "core_userreview", "core", "core_userreview.csv"
            )
            stats["provider_reviews"] = self._load_simple_table(
                "core_providerreview", "core", "core_providerreview.csv"
            )
            stats["admin_log"] = self._load_admin_log(users)
            token_stats = self._load_tokens(users)
            self._reset_sequences()

        self.stdout.write(self.style.SUCCESS("CSV seed data loaded successfully."))
        for key, value in stats.items():
            self.stdout.write(f"  {key.replace('_', ' ').title()}: {value}")
        self.stdout.write(
            f"  JWT outstanding / blacklisted: {token_stats['outstanding']} / {token_stats['blacklisted']}"
        )
        self.stdout.write("")
        self.stdout.write(self.style.WARNING(f"Login password for all users: {password}"))

    def _clear(self) -> None:
        self.stdout.write("Clearing seeded data…")
        if connection.vendor == "postgresql":
            tables = ", ".join(CLEAR_TABLES)
            with connection.cursor() as cursor:
                cursor.execute(f"TRUNCATE {tables} RESTART IDENTITY CASCADE")
        else:
            with connection.cursor() as cursor:
                for table in CLEAR_TABLES:
                    cursor.execute(f"DELETE FROM {table}")
        BlacklistedToken.objects.all().delete()
        OutstandingToken.objects.all().delete()
        LogEntry.objects.all().delete()
        User.objects.all().delete()
        Group.objects.all().delete()

    def _permission(
        self,
        codename: str,
        app_label: str = "accounts",
        model: str = "user",
    ) -> Permission | None:
        try:
            content_type = ContentType.objects.get(app_label=app_label, model=model)
        except ContentType.DoesNotExist:
            return None
        return Permission.objects.filter(content_type=content_type, codename=codename).first()

    def _load_groups(self) -> dict[int, Group]:
        rows = _read_csv(_csv_path("auth", "auth_group.csv"))
        groups: dict[int, Group] = {}
        for row in rows:
            pk = int(row["id"])
            group, _ = Group.objects.update_or_create(id=pk, defaults={"name": row["name"]})
            groups[pk] = group
        self._groups_cache = groups
        return groups

    def _load_users(self, password: str) -> dict[int, User]:
        rows = _read_csv(_csv_path("accounts", "accounts_user.csv"))
        users: dict[int, User] = {}
        for row in rows:
            pk = int(row["id"])
            birth_raw = row.get("birth_date", "").strip()
            birth_date = parse_date(birth_raw) if birth_raw else None

            user, _ = User.objects.update_or_create(
                id=pk,
                defaults={
                    "email": row["email"],
                    "first_name": row["first_name"],
                    "last_name": row["last_name"],
                    "is_superuser": _parse_bool(row["is_superuser"]),
                    "is_staff": _parse_bool(row["is_staff"]),
                    "is_active": _parse_bool(row["is_active"]),
                    "last_login": _parse_dt(row.get("last_login")),
                    "date_joined": _parse_dt(row["date_joined"]) or timezone.now(),
                    "phone_number": row.get("phone_number", ""),
                    "birth_date": birth_date,
                    "social_security_number": row.get("social_security_number", ""),
                    "role": row.get("role") or User.Role.CUSTOMER,
                    "totp_confirmed": False,
                    "totp_secret": "",
                    "sms_2fa_enabled": False,
                    "cnp_lookup_hash": "",
                },
            )
            user.set_password(password)
            user.save(update_fields=["password"])
            users[pk] = user
        return users

    def _load_simple_table(self, table: str, folder: str, filename: str) -> int:
        path = _optional_csv_path(folder, filename)
        if not path:
            return 0
        rows = _read_csv(path)
        if not rows:
            return 0

        columns = list(rows[0].keys())
        placeholders = ", ".join(["%s"] * len(columns))
        col_sql = ", ".join(columns)
        update_sql = ", ".join(f"{col}=EXCLUDED.{col}" for col in columns if col != "id")
        sql = (
            f"INSERT INTO {table} ({col_sql}) VALUES ({placeholders}) "
            f"ON CONFLICT (id) DO UPDATE SET {update_sql}"
        )

        with connection.cursor() as cursor:
            for row in rows:
                values = []
                for col in columns:
                    raw = row.get(col, "")
                    if raw == "":
                        if col.endswith("_id") or col.endswith("_at") or col in {
                            "last_login",
                            "birth_date",
                            "valid_from",
                            "valid_until",
                            "paid_at",
                            "issued_at",
                            "due_at",
                            "confirmed_at",
                            "completed_at",
                            "cancelled_at",
                            "owner_user_id",
                            "booking_id",
                            "service_id",
                            "rule_id",
                            "invoice_id",
                            "customer_availability_id",
                            "provider_availability_id",
                            "service_link_id",
                        }:
                            values.append(None)
                        else:
                            values.append("")
                        continue
                    if col.endswith("_at") or col in {"last_login", "date_joined", "paid_at", "issued_at", "due_at"}:
                        values.append(_parse_dt(raw))
                    elif col.endswith("_date") or col in {"valid_from", "valid_until", "birth_date"}:
                        values.append(parse_date(raw) if raw else None)
                    elif col.endswith("_time"):
                        values.append(raw)
                    elif col in {
                        "latitude",
                        "longitude",
                        "min_price",
                        "max_price",
                        "price",
                        "price_min",
                        "price_max",
                        "travel_km",
                        "provider_price",
                        "amount",
                        "subtotal",
                        "tax",
                        "total",
                        "travel_radius_km",
                    }:
                        values.append(_parse_decimal(raw))
                    elif col in {
                        "duration_minutes",
                        "travel_time_minutes",
                        "weekday",
                        "rating",
                    } or col.endswith("_id") and col != "external_reference":
                        values.append(_parse_int(raw))
                    elif col.startswith("is_") or col in {"totp_confirmed", "sms_2fa_enabled"}:
                        values.append(_parse_bool(raw))
                    else:
                        values.append(raw)
                cursor.execute(sql, values)
        return len(rows)

    def _load_user_groups(self, users: dict[int, User], groups: dict[int, Group]) -> None:
        rows = _read_csv(_csv_path("accounts", "accounts_user_groups.csv"))
        memberships: dict[int, list[Group]] = {}
        for row in rows:
            user = users.get(int(row["user_id"]))
            group = groups.get(int(row["group_id"]))
            if user and group:
                memberships.setdefault(user.pk, []).append(group)
        for user_id, member_groups in memberships.items():
            users[user_id].groups.set(member_groups)

    def _load_group_permissions(self, groups: dict[int, Group]) -> None:
        rows = _read_csv(_csv_path("auth", "auth_group_permissions.csv"))
        by_group: dict[int, list[Permission]] = {}
        for row in rows:
            gid = int(row["group_id"])
            perm = self._permission(
                row["permission_codename"],
                row.get("content_type_app") or "accounts",
                row.get("content_type_model") or "user",
            )
            if perm:
                by_group.setdefault(gid, []).append(perm)
        for gid, perms in by_group.items():
            if gid in groups:
                groups[gid].permissions.set(perms)

    def _load_user_permissions(self, users: dict[int, User]) -> None:
        path = _optional_csv_path("accounts", "accounts_user_user_permissions.csv")
        if not path:
            return
        rows = _read_csv(path)
        by_user: dict[int, list[Permission]] = {}
        for row in rows:
            uid = int(row["user_id"])
            perm = self._permission(
                row["permission_codename"],
                row.get("content_type_app") or "accounts",
                row.get("content_type_model") or "user",
            )
            if perm:
                by_user.setdefault(uid, []).append(perm)
        for uid, perms in by_user.items():
            if uid in users:
                users[uid].user_permissions.set(perms)

    def _load_admin_log(self, users: dict[int, User]) -> int:
        path = _optional_csv_path("django", "django_admin_log.csv")
        if not path:
            return 0
        rows = _read_csv(path)
        user_ct = ContentType.objects.get_for_model(User)
        count = 0
        for row in rows:
            actor = users.get(int(row["user_id"]))
            if not actor:
                continue
            LogEntry.objects.update_or_create(
                id=int(row["id"]),
                defaults={
                    "action_time": _parse_dt(row["action_time"]) or timezone.now(),
                    "object_id": row.get("object_id") or str(row["id"]),
                    "object_repr": row["object_repr"],
                    "action_flag": ACTION_FLAG_MAP.get(str(row["action_flag"]), CHANGE),
                    "change_message": row["change_message"],
                    "content_type": user_ct,
                    "user": actor,
                },
            )
            count += 1
        return count

    def _load_tokens(self, users: dict[int, User]) -> dict[str, int]:
        outstanding_path = _optional_csv_path("token_blacklist", "token_blacklist_outstandingtoken.csv")
        if not outstanding_path:
            return {"outstanding": 0, "blacklisted": 0}

        outstanding_rows = _read_csv(outstanding_path)
        token_by_id: dict[int, OutstandingToken] = {}
        for row in outstanding_rows:
            user = users.get(int(row["user_id"]))
            if not user:
                continue
            token, _ = OutstandingToken.objects.update_or_create(
                id=int(row["id"]),
                defaults={
                    "user": user,
                    "jti": row["jti"],
                    "token": row["token"],
                    "created_at": _parse_dt(row["created_at"]) or timezone.now(),
                    "expires_at": _parse_dt(row["expires_at"]) or timezone.now(),
                },
            )
            token_by_id[int(row["id"])] = token

        blacklisted = 0
        bl_path = _optional_csv_path("token_blacklist", "token_blacklist_blacklistedtoken.csv")
        if bl_path:
            for row in _read_csv(bl_path):
                outstanding = token_by_id.get(int(row.get("token_id") or row.get("outstanding_token_id", 0)))
                if not outstanding:
                    continue
                _, created = BlacklistedToken.objects.update_or_create(
                    token=outstanding,
                    defaults={
                        "blacklisted_at": _parse_dt(row["blacklisted_at"]) or timezone.now(),
                    },
                )
                if created:
                    blacklisted += 1

        return {"outstanding": len(token_by_id), "blacklisted": blacklisted}

    def _reset_sequences(self) -> None:
        if connection.vendor != "postgresql":
            return
        with connection.cursor() as cursor:
            for table in SEQUENCE_TABLES:
                cursor.execute(
                    "SELECT setval(pg_get_serial_sequence(%s, 'id'), "
                    "COALESCE((SELECT MAX(id) FROM {}), 1))".format(table),
                    [table],
                )
