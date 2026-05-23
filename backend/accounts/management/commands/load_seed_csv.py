"""
Load seed data from backend/db/**/*.csv into PostgreSQL.

Usage (from backend/):
    uv run python manage.py migrate
    uv run python manage.py load_seed_csv
    uv run python manage.py load_seed_csv --clear
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from accounts.models import User

DB_ROOT = Path(settings.BASE_DIR) / "db"
DEFAULT_PASSWORD = "CarePath2026!"

ACTION_FLAG_MAP = {
    "1": ADDITION,
    "2": CHANGE,
    "3": DELETION,
}


def _csv_path(*parts: str) -> Path:
    path = DB_ROOT.joinpath(*parts)
    if not path.is_file():
        raise CommandError(f"Missing seed file: {path}")
    return path


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


class Command(BaseCommand):
    help = "Load seed CSV files from backend/db/ into the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing seeded rows before loading CSV data.",
        )
        parser.add_argument(
            "--password",
            default=DEFAULT_PASSWORD,
            help=f"Password applied to all loaded users (default: {DEFAULT_PASSWORD}).",
        )

    def handle(self, *args, **options):
        if not DB_ROOT.is_dir():
            raise CommandError(f"Seed directory not found: {DB_ROOT}")

        password: str = options["password"]
        if options["clear"]:
            self._clear()

        with transaction.atomic():
            groups = self._load_groups()
            users = self._load_users(password)
            self._load_user_groups(users, groups)
            self._load_group_permissions(groups)
            self._load_user_permissions(users)
            log_count = self._load_admin_log(users)
            token_stats = self._load_tokens(users)
            self._reset_sequences()

        self.stdout.write(self.style.SUCCESS("CSV seed data loaded successfully."))
        self.stdout.write(f"  Users: {len(users)}")
        self.stdout.write(f"  Groups: {len(groups)}")
        self.stdout.write(
            f"  JWT outstanding / blacklisted: {token_stats['outstanding']} / {token_stats['blacklisted']}"
        )
        self.stdout.write(f"  Admin log entries: {log_count}")
        self.stdout.write("")
        self.stdout.write(self.style.WARNING(f"Login password for all users: {password}"))

    def _clear(self) -> None:
        self.stdout.write("Clearing seeded data…")
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
        return groups

    def _load_users(self, password: str) -> dict[int, User]:
        rows = _read_csv(_csv_path("accounts", "accounts_user.csv"))
        users: dict[int, User] = {}
        for row in rows:
            pk = int(row["id"])
            birth_raw = row.get("birth_date", "").strip()
            birth_date = None
            if birth_raw:
                birth_date = datetime.strptime(birth_raw, "%Y-%m-%d").date()

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
                },
            )
            user.set_password(password)
            user.save(update_fields=["password"])
            users[pk] = user
        return users

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
        path = _csv_path("accounts", "accounts_user_user_permissions.csv")
        if not path.is_file():
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
        rows = _read_csv(_csv_path("django", "django_admin_log.csv"))
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
                    "object_id": row["object_id"],
                    "object_repr": row["object_repr"],
                    "action_flag": ACTION_FLAG_MAP.get(row["action_flag"], CHANGE),
                    "change_message": row["change_message"],
                    "content_type": user_ct,
                    "user": actor,
                },
            )
            count += 1
        return count

    def _load_tokens(self, users: dict[int, User]) -> dict[str, int]:
        outstanding_rows = _read_csv(_csv_path("token_blacklist", "token_blacklist_outstandingtoken.csv"))
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
        bl_rows = _read_csv(_csv_path("token_blacklist", "token_blacklist_blacklistedtoken.csv"))
        for row in bl_rows:
            outstanding = token_by_id.get(int(row["token_id"]))
            if not outstanding:
                continue
            _, created = BlacklistedToken.objects.update_or_create(
                id=int(row["id"]),
                defaults={
                    "token": outstanding,
                    "blacklisted_at": _parse_dt(row["blacklisted_at"]) or timezone.now(),
                },
            )
            if created:
                blacklisted += 1

        return {"outstanding": len(token_by_id), "blacklisted": blacklisted}

    def _reset_sequences(self) -> None:
        if connection.vendor != "postgresql":
            return
        tables = (
            ("accounts_user", "id"),
            ("auth_group", "id"),
            ("django_admin_log", "id"),
            ("token_blacklist_outstandingtoken", "id"),
            ("token_blacklist_blacklistedtoken", "id"),
        )
        with connection.cursor() as cursor:
            for table, column in tables:
                cursor.execute(
                    "SELECT setval(pg_get_serial_sequence(%s, %s), "
                    "COALESCE((SELECT MAX(id) FROM {}), 1))".format(table),
                    [table, column],
                )
