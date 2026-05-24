"""Generate a plain SQL file (db/migrate_medical.sql) from the medical CSVs.

The output contains UPDATE statements that overwrite the textual / pricing
fields of the medical-themed tables in PostgreSQL. Run it from `backend/`:

    python scripts/generate_medical_sql.py

Then open `backend/db/migrate_medical.sql` in DBeaver and execute it.
"""

from __future__ import annotations

import csv
from pathlib import Path
from textwrap import dedent

BACKEND_DIR = Path(__file__).resolve().parents[1]
DB_ROOT = BACKEND_DIR / "db"
OUT_FILE = DB_ROOT / "migrate_medical.sql"


def quote(value: str) -> str:
    if value == "" or value is None:
        return "NULL"
    return "'" + value.replace("'", "''") + "'"


def num(value: str) -> str:
    return value if value not in (None, "") else "NULL"


def boolean(value: str) -> str:
    return "TRUE" if str(value).strip().lower() in {"true", "1", "yes", "t"} else "FALSE"


def read_rows(name: str) -> list[dict[str, str]]:
    path = DB_ROOT / name
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def emit_services() -> list[str]:
    out = ["-- core_service (medical catalog)"]
    for row in read_rows("core/core_service.csv"):
        out.append(
            "UPDATE core_service SET "
            f"name={quote(row['name'])}, "
            f"slug={quote(row['slug'])}, "
            f"description={quote(row['description'])}, "
            f"min_price={num(row['min_price'])}, "
            f"max_price={num(row['max_price'])}, "
            f"is_active={boolean(row['is_active'])} "
            f"WHERE id={row['id']};"
        )
    return out


def emit_provider_profiles() -> list[str]:
    out = ["", "-- core_providerprofile (medical professions)"]
    for row in read_rows("core/core_providerprofile.csv"):
        out.append(
            "UPDATE core_providerprofile SET "
            f"display_name={quote(row['display_name'])}, "
            f"bio={quote(row['bio'])}, "
            f"is_active={boolean(row['is_active'])} "
            f"WHERE id={row['id']};"
        )
    return out


def emit_user_profiles() -> list[str]:
    out = ["", "-- core_userprofile (medical interests)"]
    for row in read_rows("core/core_userprofile.csv"):
        out.append(
            "UPDATE core_userprofile SET "
            f"bio={quote(row['bio'])} "
            f"WHERE id={row['id']};"
        )
    return out


def emit_user_reviews() -> list[str]:
    out = ["", "-- core_userreview (medical-themed feedback)"]
    for row in read_rows("core/core_userreview.csv"):
        out.append(
            "UPDATE core_userreview SET "
            f"comment={quote(row['comment'])} "
            f"WHERE id={row['id']};"
        )
    return out


def emit_provider_reviews() -> list[str]:
    out = ["", "-- core_providerreview (medical-themed feedback)"]
    for row in read_rows("core/core_providerreview.csv"):
        out.append(
            "UPDATE core_providerreview SET "
            f"comment={quote(row['comment'])} "
            f"WHERE id={row['id']};"
        )
    return out


def main() -> None:
    header = dedent(
        """\
        -- Refresh the BitHealth catalog so it only contains medical content.
        -- Generated from backend/db/core/*.csv via scripts/generate_medical_sql.py
        -- Run inside DBeaver against the same Postgres DB used by Django.

        BEGIN;
        """
    ).splitlines()
    footer = ["", "COMMIT;", ""]
    lines: list[str] = []
    lines.extend(header)
    lines.extend(emit_services())
    lines.extend(emit_provider_profiles())
    lines.extend(emit_user_profiles())
    lines.extend(emit_user_reviews())
    lines.extend(emit_provider_reviews())
    lines.extend(footer)

    OUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_FILE}")


if __name__ == "__main__":
    main()
