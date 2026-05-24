"""TRUNCATE + reload all application tables from backend/db/ CSVs.

This script wipes every duplicate / orphan row by truncating all the seeded
application tables (Django auth/system tables are left alone) and then
reloads them from the CSV seed files in dependency order, so DBeaver shows
exactly what the CSVs contain.

Run from the `backend/` folder:

    python scripts/reset_and_seed_db.py
"""

from __future__ import annotations

import csv
import os
import sys
from decimal import Decimal
from pathlib import Path

import django

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db import connection  # noqa: E402
from django.utils import timezone  # noqa: E402
from django.utils.dateparse import parse_date, parse_datetime  # noqa: E402

DB_ROOT = BACKEND_DIR / "db"

DECIMAL_COLUMNS: set[str] = {
    "min_price",
    "max_price",
    "provider_price",
    "travel_radius_km",
    "travel_km",
    "price",
    "price_min",
    "price_max",
    "subtotal",
    "tax",
    "total",
    "amount",
    "latitude",
    "longitude",
}
BOOLEAN_COLUMNS: set[str] = {
    "is_active",
    "is_superuser",
    "is_staff",
}
DATE_ONLY_COLUMNS: set[str] = {
    "valid_from",
    "valid_until",
    "birth_date",
}
INTEGER_COLUMNS: set[str] = {
    "rating",
    "weekday",
    "duration_minutes",
    "travel_time_minutes",
}

TRUNCATE_TARGETS: list[str] = [
    "core_userreview",
    "core_providerreview",
    "fact_payments",
    "invoices",
    "fact_bookings",
    "availability_providers",
    "availability_rule",
    "availability_customers",
    "core_serviceprovider",
    "core_service",
    "core_userprofile",
    "core_providerprofile",
    "core_geolocation",
    "accounts_user_languages",
    "accounts_user_groups",
    "accounts_user_user_permissions",
    "accounts_user",
    "core_language",
]

# (table, csv_path_relative_to_db_root, optional defaults dict for missing cols)
LOAD_PLAN: list[tuple[str, str, dict[str, object]]] = [
    ("core_language", "core/core_language.csv", {}),
    (
        "accounts_user",
        "accounts/accounts_user.csv",
        {
            "password": "!unusable",
            "social_security_number": "",
            "totp_confirmed": False,
            "totp_secret": "",
            "sms_2fa_enabled": False,
            "cnp_lookup_hash": "",
        },
    ),
    ("core_geolocation", "core/core_geolocation.csv", {}),
    ("core_userprofile", "core/core_userprofile.csv", {}),
    ("core_providerprofile", "core/core_providerprofile.csv", {}),
    ("core_service", "core/core_service.csv", {}),
    ("core_serviceprovider", "core/core_serviceprovider.csv", {}),
    ("availability_rule", "availability/availability_rule.csv", {}),
    ("availability_providers", "availability/availability_providers.csv", {}),
    ("availability_customers", "availability/availability_customers.csv", {}),
    ("fact_bookings", "fact/fact_bookings.csv", {}),
    ("invoices", "fact/invoices.csv", {}),
    ("fact_payments", "fact/fact_payments.csv", {}),
    ("core_userreview", "core/core_userreview.csv", {}),
    ("core_providerreview", "core/core_providerreview.csv", {}),
    ("accounts_user_languages", "accounts/accounts_user_languages.csv", {}),
]


def parse_dt(raw: str):
    if not raw:
        return None
    parsed = parse_datetime(raw.strip())
    if parsed and timezone.is_naive(parsed):
        return timezone.make_aware(parsed)
    return parsed


def coerce(column: str, raw: str):
    if raw is None or raw == "":
        if column in BOOLEAN_COLUMNS:
            return False
        if (
            column.endswith("_id")
            or column.endswith("_at")
            or column in DATE_ONLY_COLUMNS
            or column in DECIMAL_COLUMNS
            or column in INTEGER_COLUMNS
        ):
            return None
        return ""

    raw = raw.strip()
    if column in BOOLEAN_COLUMNS:
        return raw.lower() in {"true", "t", "1", "yes"}
    if column in DATE_ONLY_COLUMNS:
        return parse_date(raw)
    if column.endswith("_at"):
        return parse_dt(raw)
    if column in DECIMAL_COLUMNS:
        return Decimal(raw)
    if column in INTEGER_COLUMNS:
        return int(float(raw))
    if column.endswith("_id") or column == "id":
        return int(raw)
    return raw


def truncate_all() -> None:
    targets = ", ".join(TRUNCATE_TARGETS)
    sql = f"TRUNCATE {targets} RESTART IDENTITY CASCADE"
    with connection.cursor() as cur:
        cur.execute(sql)
    print(f"  [truncated] {len(TRUNCATE_TARGETS)} tables (RESTART IDENTITY CASCADE)")


def load_table(table: str, csv_rel: str, extra_defaults: dict[str, object]) -> int:
    csv_path = DB_ROOT / csv_rel
    if not csv_path.exists():
        print(f"  [warn] missing {csv_path}")
        return 0
    rows = list(csv.DictReader(csv_path.open(newline="", encoding="utf-8")))
    if not rows:
        print(f"  [skip] {csv_rel}: no rows")
        return 0

    csv_columns = list(rows[0].keys())
    csv_column_set = set(csv_columns)
    extra_columns = [c for c in extra_defaults.keys() if c not in csv_column_set]
    columns = csv_columns + extra_columns
    placeholders = ", ".join(["%s"] * len(columns))
    col_sql = ", ".join(columns)
    sql = f"INSERT INTO {table} ({col_sql}) VALUES ({placeholders})"

    with connection.cursor() as cur:
        for row in rows:
            values = [coerce(col, row.get(col, "")) for col in csv_columns]
            values.extend(extra_defaults[col] for col in extra_columns)
            cur.execute(sql, values)
        cur.execute(
            f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
            f"COALESCE((SELECT MAX(id) FROM {table}), 1))"
        )
    return len(rows)


def main() -> None:
    print("Resetting application tables...")
    truncate_all()
    print()
    print("Reloading from CSVs (in dependency order)...")
    for table, csv_rel, defaults in LOAD_PLAN:
        count = load_table(table, csv_rel, defaults)
        print(f"  [ok] {table}: {count} rows from {csv_rel}")
    print()
    print("Done. Refresh tables in DBeaver to see the clean data.")


if __name__ == "__main__":
    main()
