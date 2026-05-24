"""Check the seed CSVs for FK references that point to IDs that won't exist after reload."""

from __future__ import annotations

import csv
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / "db"


def ids_in(rel: str) -> set[int]:
    path = DB / rel
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    return {int(r["id"]) for r in rows}


def references(rel: str, columns: dict[str, set[int]]) -> int:
    path = DB / rel
    if not path.exists():
        print(f"[skip] missing {rel}")
        return 0
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    bad_total = 0
    for col, valid_ids in columns.items():
        bad = [
            (r["id"], r[col])
            for r in rows
            if r.get(col, "").strip() and int(r[col]) not in valid_ids
        ]
        if bad:
            bad_total += len(bad)
            summary = bad[:8]
            more = "" if len(bad) <= 8 else f" (+{len(bad) - 8} more)"
            print(f"[bad] {rel}: column {col} -> {summary}{more}")
    return bad_total


def main() -> None:
    user_ids = ids_in("accounts/accounts_user.csv")
    geo_ids = ids_in("core/core_geolocation.csv")
    lang_ids = ids_in("core/core_language.csv")
    service_ids = ids_in("core/core_service.csv")
    provider_profile_ids = ids_in("core/core_providerprofile.csv")
    booking_ids = ids_in("fact/fact_bookings.csv")
    invoice_ids = ids_in("fact/invoices.csv")
    rule_ids = ids_in("availability/availability_rule.csv")
    avail_provider_ids = ids_in("availability/availability_providers.csv")
    avail_customer_ids = ids_in("availability/availability_customers.csv")
    service_link_ids = ids_in("core/core_serviceprovider.csv")

    print(f"Seeded IDs — users:{len(user_ids)} geos:{len(geo_ids)} langs:{len(lang_ids)} services:{len(service_ids)} providers:{len(provider_profile_ids)}")
    print(f"            bookings:{len(booking_ids)} invoices:{len(invoice_ids)} rules:{len(rule_ids)}")

    bad = 0
    bad += references(
        "accounts/accounts_user_languages.csv",
        {"user_id": user_ids, "language_id": lang_ids},
    )
    bad += references(
        "core/core_userprofile.csv",
        {"user_id": user_ids, "home_location_id": geo_ids},
    )
    bad += references(
        "core/core_providerprofile.csv",
        {"user_id": user_ids, "service_area_id": geo_ids},
    )
    bad += references(
        "core/core_serviceprovider.csv",
        {"service_id": service_ids, "provider_id": provider_profile_ids},
    )
    bad += references(
        "availability/availability_rule.csv",
        {"provider_id": provider_profile_ids},
    )
    bad += references(
        "availability/availability_providers.csv",
        {
            "provider_id": provider_profile_ids,
            "service_id": service_ids,
            "rule_id": rule_ids,
        },
    )
    bad += references(
        "availability/availability_customers.csv",
        {"customer_id": user_ids},
    )
    bad += references(
        "fact/fact_bookings.csv",
        {
            "service_id": service_ids,
            "provider_id": provider_profile_ids,
            "customer_id": user_ids,
            "visit_location_id": geo_ids,
            "service_link_id": service_link_ids,
            "provider_availability_id": avail_provider_ids,
            "customer_availability_id": avail_customer_ids,
        },
    )
    bad += references(
        "fact/invoices.csv",
        {"booking_id": booking_ids, "customer_id": user_ids, "provider_id": provider_profile_ids},
    )
    bad += references(
        "fact/fact_payments.csv",
        {"booking_id": booking_ids, "invoice_id": invoice_ids},
    )
    bad += references(
        "core/core_userreview.csv",
        {"reviewer_id": user_ids, "provider_id": provider_profile_ids, "booking_id": booking_ids},
    )
    bad += references(
        "core/core_providerreview.csv",
        {"reviewer_id": user_ids, "customer_id": user_ids, "booking_id": booking_ids},
    )

    if bad == 0:
        print("All FK references resolve to seeded IDs.")
    else:
        print(f"\nFound {bad} bad references — fix these before TRUNCATE+RELOAD.")


if __name__ == "__main__":
    main()
