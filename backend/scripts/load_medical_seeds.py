"""Load the medical-themed CSVs into PostgreSQL (UPSERT by id).

This script refreshes the rows in:
    - core_service
    - core_providerprofile
    - core_userprofile
    - core_userreview
    - core_providerreview

So that the DB (visible in DBeaver) only contains medical-personnel data
matching the CSVs in backend/db/.

Usage (from `backend/`):

    # PowerShell — make sure backend/.env has PG* and DJANGOSECRET set
    python scripts/load_medical_seeds.py
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
from django.utils.dateparse import parse_datetime  # noqa: E402


DECIMAL_COLUMNS: dict[str, set[str]] = {
    "core_service": {"min_price", "max_price"},
    "core_providerprofile": {"travel_radius_km"},
}
BOOLEAN_COLUMNS: dict[str, set[str]] = {
    "core_service": {"is_active"},
    "core_providerprofile": {"is_active"},
}


def parse_dt(raw: str):
    if not raw:
        return None
    parsed = parse_datetime(raw.strip())
    if parsed and timezone.is_naive(parsed):
        return timezone.make_aware(parsed)
    return parsed


def coerce(table: str, column: str, raw: str):
    if raw == "":
        if column.endswith("_id") or column.endswith("_at"):
            return None
        if column in BOOLEAN_COLUMNS.get(table, set()):
            return None
        if column in DECIMAL_COLUMNS.get(table, set()):
            return None
        return ""
    if column.endswith("_at"):
        return parse_dt(raw)
    if column in BOOLEAN_COLUMNS.get(table, set()):
        return raw.strip().lower() in {"true", "t", "1", "yes"}
    if column in DECIMAL_COLUMNS.get(table, set()):
        return Decimal(raw)
    if column == "rating":
        return int(raw)
    if column.endswith("_id") or column == "id":
        return int(raw)
    return raw


def upsert_csv(csv_path: Path, table: str) -> int:
    rows = list(csv.DictReader(csv_path.open(newline="", encoding="utf-8")))
    if not rows:
        print(f"  [skip] {csv_path.name}: no rows")
        return 0

    columns = list(rows[0].keys())
    placeholders = ", ".join(["%s"] * len(columns))
    col_sql = ", ".join(columns)
    update_sql = ", ".join(f"{c}=EXCLUDED.{c}" for c in columns if c != "id")
    sql = (
        f"INSERT INTO {table} ({col_sql}) VALUES ({placeholders}) "
        f"ON CONFLICT (id) DO UPDATE SET {update_sql}"
    )

    with connection.cursor() as cursor:
        for row in rows:
            values = [coerce(table, col, row.get(col, "")) for col in columns]
            cursor.execute(sql, values)
        cursor.execute(
            f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
            f"COALESCE((SELECT MAX(id) FROM {table}), 1))"
        )
    return len(rows)


def main() -> None:
    db_root = BACKEND_DIR / "db"
    plan: list[tuple[Path, str]] = [
        (db_root / "core" / "core_service.csv", "core_service"),
        (db_root / "core" / "core_providerprofile.csv", "core_providerprofile"),
        (db_root / "core" / "core_userprofile.csv", "core_userprofile"),
        (db_root / "core" / "core_userreview.csv", "core_userreview"),
        (db_root / "core" / "core_providerreview.csv", "core_providerreview"),
    ]

    print("Loading medical seed CSVs into PostgreSQL...")
    for csv_path, table in plan:
        if not csv_path.exists():
            print(f"  [warn] missing CSV: {csv_path}")
            continue
        count = upsert_csv(csv_path, table)
        print(f"  [ok] {table}: {count} rows upserted from {csv_path.name}")
    print("Done. Refresh the tables in DBeaver to see the new data.")


if __name__ == "__main__":
    main()
