"""Load core_geolocation.csv into PostgreSQL (upsert by id)."""

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


def parse_dt(raw: str):
    if not raw:
        return None
    parsed = parse_datetime(raw.strip())
    if parsed and timezone.is_naive(parsed):
        return timezone.make_aware(parsed)
    return parsed


def main() -> None:
    path = BACKEND_DIR / "db" / "core" / "core_geolocation.csv"
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        print("No rows found.")
        return

    columns = list(rows[0].keys())
    placeholders = ", ".join(["%s"] * len(columns))
    col_sql = ", ".join(columns)
    update_sql = ", ".join(f"{col}=EXCLUDED.{col}" for col in columns if col != "id")
    sql = (
        f"INSERT INTO core_geolocation ({col_sql}) VALUES ({placeholders}) "
        f"ON CONFLICT (id) DO UPDATE SET {update_sql}"
    )

    with connection.cursor() as cursor:
        for row in rows:
            values = []
            for col in columns:
                raw = row.get(col, "")
                if raw == "":
                    if col.endswith("_id") or col.endswith("_at"):
                        values.append(None)
                    else:
                        values.append("")
                    continue
                if col.endswith("_at"):
                    values.append(parse_dt(raw))
                elif col in {"latitude", "longitude"}:
                    values.append(Decimal(raw))
                elif col.endswith("_id"):
                    values.append(int(raw))
                else:
                    values.append(raw)
            cursor.execute(sql, values)

        cursor.execute(
            "SELECT setval(pg_get_serial_sequence('core_geolocation', 'id'), "
            "COALESCE((SELECT MAX(id) FROM core_geolocation), 1))"
        )
        cursor.execute("SELECT COUNT(*) FROM core_geolocation")
        count = cursor.fetchone()[0]

    print(f"Loaded/updated {len(rows)} geolocation rows. Table now has {count} rows.")


if __name__ == "__main__":
    main()
