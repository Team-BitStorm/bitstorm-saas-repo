"""
Transform Romanian CSV exports into backend/db/ seed files.

Usage:
    python scripts/build_seed_csvs.py
    python scripts/build_seed_csvs.py "C:/path/to/csv_data"
"""

from __future__ import annotations

import csv
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

DEFAULT_SRC = Path(r"C:\Users\vlad\Downloads\csv_data_romana\csv_data")
DB_ROOT = Path(__file__).resolve().parents[1] / "db"

PERM_CSV_TO_DJANGO: dict[str, tuple[str, str, str]] = {
    "add_user": ("accounts", "user", "add_user"),
    "change_user": ("accounts", "user", "change_user"),
    "delete_user": ("accounts", "user", "delete_user"),
    "view_user": ("accounts", "user", "view_user"),
    "add_service": ("core", "service", "add_service"),
    "change_service": ("core", "service", "change_service"),
    "delete_service": ("core", "service", "delete_service"),
    "view_service": ("core", "service", "view_service"),
    "add_booking": ("core", "factbooking", "add_factbooking"),
    "change_booking": ("core", "factbooking", "change_booking"),
    "delete_booking": ("core", "factbooking", "delete_booking"),
    "view_booking": ("core", "factbooking", "view_factbooking"),
    "add_review": ("core", "userreview", "add_userreview"),
    "change_review": ("core", "userreview", "change_userreview"),
    "delete_review": ("core", "userreview", "delete_userreview"),
    "view_review": ("core", "userreview", "view_userreview"),
    "add_provider": ("core", "providerprofile", "add_providerprofile"),
    "change_provider": ("core", "providerprofile", "change_providerprofile"),
    "delete_provider": ("core", "providerprofile", "delete_providerprofile"),
    "view_provider": ("core", "providerprofile", "view_providerprofile"),
    "add_payment": ("core", "factpayment", "add_factpayment"),
    "change_payment": ("core", "factpayment", "change_factpayment"),
    "delete_payment": ("core", "factpayment", "delete_factpayment"),
    "view_payment": ("core", "factpayment", "view_factpayment"),
    "add_geolocation": ("core", "geolocation", "add_geolocation"),
    "view_geolocation": ("core", "geolocation", "view_geolocation"),
    "add_language": ("core", "language", "add_language"),
    "view_language": ("core", "language", "view_language"),
    "manage_permissions": ("auth", "permission", "view_permission"),
    "admin_panel": ("admin", "logentry", "view_logentry"),
}

BOOKING_STATUS = {
    "în așteptare": "pending",
    "confirmat": "confirmed",
    "finalizat": "completed",
    "anulat": "cancelled",
    "nerealizat": "declined",
}
PAYMENT_STATUS = {
    "în procesare": "pending",
    "eșuat": "failed",
    "reușit": "completed",
    "plătit": "completed",
    "platit": "completed",
    "finalizat": "completed",
}
PAYMENT_METHOD = {
    "numerar": "cash",
    "cash": "cash",
    "card": "card",
    "transfer": "transfer",
    "transfer bancar": "transfer",
}
INVOICE_STATUS = {
    "anulată": "void",
    "anulata": "void",
    "emisa": "issued",
    "emisă": "issued",
    "plătită": "paid",
    "platita": "paid",
    "draft": "draft",
}
ROLE_MAP = {
    "client": "customer",
    "provider": "provider",
    "prestator": "provider",
    "ambele": "customer",
}
WEEKDAY_MAP = {
    "luni": 0,
    "marți": 1,
    "marti": 1,
    "miercuri": 2,
    "joi": 3,
    "vineri": 4,
    "sâmbătă": 5,
    "sambata": 5,
    "duminică": 6,
    "duminica": 6,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "item"


def payment_method(raw: str) -> str:
    key = (raw or "").strip().lower()
    if key in PAYMENT_METHOD:
        return PAYMENT_METHOD[key]
    if key in {"google pay", "paypal", "revolut", "apple pay"}:
        return "card"
    return "card"


def booking_ends_at(starts: str, duration_minutes: int) -> str:
    try:
        start_dt = datetime.fromisoformat(starts.replace(" ", "T", 1))
    except ValueError:
        return starts
    return (start_dt + timedelta(minutes=duration_minutes)).strftime("%Y-%m-%d %H:%M:%S")


def phone_ro(raw: str, uid: int) -> str:
    digits = re.sub(r"\D", "", raw or "")
    if digits.startswith("40"):
        digits = digits[2:]
    if digits.startswith("0"):
        digits = digits[1:]
    if len(digits) < 9:
        digits = f"7{(uid % 9) + 1}{uid:07d}"[:9]
    return f"+40 {digits[:3]} {digits[3:6]} {digits[6:9]}"


def build(src: Path, dest: Path) -> None:
    users_src = read_csv(src / "accounts_user.csv")
    profiles = {int(r["user_id"]): r for r in read_csv(src / "core_userprofile.csv")}
    provider_profiles_src = read_csv(src / "core_providerprofile.csv")
    provider_user_ids = {int(r["user_id"]) for r in provider_profiles_src}

    perm_by_id = {r["id"]: r["codename"] for r in read_csv(src / "auth_permission.csv")}

    users_out = []
    seen_emails: set[str] = set()
    for row in users_src:
        uid = int(row["id"])
        profile = profiles.get(uid, {})
        role_raw = (profile.get("role") or "").lower()
        if uid in provider_user_ids:
            role = "provider"
        elif role_raw in ("provider", "prestator"):
            role = "provider"
        elif row.get("is_staff", "").lower() == "true":
            role = "provider"
        else:
            role = ROLE_MAP.get(role_raw, "customer")

        email = row["email"]
        if email in seen_emails:
            local, _, domain = email.partition("@")
            email = f"{local}+{uid}@{domain}"
        seen_emails.add(email)

        users_out.append(
            {
                "id": row["id"],
                "email": email,
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "is_superuser": row.get("is_superuser", "False"),
                "is_staff": row.get("is_staff", "False"),
                "is_active": row.get("is_active", "True"),
                "last_login": row.get("last_login", ""),
                "date_joined": row.get("date_joined", ""),
                "phone_number": phone_ro(row.get("phone", ""), uid),
                "birth_date": "",
                "social_security_number": "",
                "role": role,
            }
        )
    write_csv(dest / "accounts" / "accounts_user.csv", list(users_out[0].keys()), users_out)

    languages_src = read_csv(src / "core_language.csv")
    languages_out = [
        {"id": r["id"], "code": r["code"], "name": r["name"]} for r in languages_src
    ]
    write_csv(dest / "core" / "core_language.csv", ["id", "code", "name"], languages_out)
    lang_name_to_id = {r["name"].lower(): int(r["id"]) for r in languages_src}
    lang_name_to_id.update({r["native_name"].lower(): int(r["id"]) for r in languages_src})

    geolocations_out = []
    for row in read_csv(src / "core_geolocation.csv"):
        geolocations_out.append(
            {
                "id": row["id"],
                "label": row["city"],
                "address_line1": row.get("address", ""),
                "address_line2": "",
                "city": row["city"],
                "region": row.get("county", ""),
                "postal_code": "",
                "country": row.get("country", "România"),
                "latitude": row.get("latitude", ""),
                "longitude": row.get("longitude", ""),
                "created_at": "2024-01-01 00:00:00",
                "owner_user_id": "",
            }
        )
    write_csv(
        dest / "core" / "core_geolocation.csv",
        list(geolocations_out[0].keys()),
        geolocations_out,
    )
    geo_ids = [int(r["id"]) for r in geolocations_out]
    city_to_geo = {}
    for geo in geolocations_out:
        city_to_geo.setdefault(geo["city"].lower(), int(geo["id"]))

    def geolocation_for_user(user_id: int, city: str = "") -> str:
        if city:
            matched = city_to_geo.get(city.lower())
            if matched is not None:
                return str(matched)
        if geo_ids:
            return str(geo_ids[(user_id - 1) % len(geo_ids)])
        return "1"

    user_profiles_out = []
    seen_profile_users: set[int] = set()
    user_home_location: dict[int, str] = {}
    for row in read_csv(src / "core_userprofile.csv"):
        uid = int(row["user_id"])
        if uid in seen_profile_users:
            continue
        seen_profile_users.add(uid)
        home_location_id = geolocation_for_user(uid, row.get("city", ""))
        user_home_location[uid] = home_location_id
        user_profiles_out.append(
            {
                "id": row["id"],
                "user_id": row["user_id"],
                "avatar_url": "",
                "bio": row.get("bio", ""),
                "home_location_id": home_location_id,
            }
        )
    write_csv(
        dest / "core" / "core_userprofile.csv",
        ["id", "user_id", "avatar_url", "bio", "home_location_id"],
        user_profiles_out,
    )

    provider_profiles_out = []
    seen_provider_users: set[int] = set()
    user_names = {int(r["id"]): f"{r['first_name']} {r['last_name']}" for r in users_src}
    for row in provider_profiles_src:
        uid = int(row["user_id"])
        if uid in seen_provider_users:
            continue
        seen_provider_users.add(uid)
        provider_profiles_out.append(
            {
                "id": row["id"],
                "user_id": row["user_id"],
                "display_name": f"{row.get('profession', 'Prestator')} — {user_names.get(uid, uid)}",
                "bio": row.get("bio", ""),
                "is_active": "True" if row.get("is_verified", "").lower() == "true" else "True",
                "service_area_id": geolocation_for_user(uid),
                "travel_radius_km": row.get("years_experience", "15"),
            }
        )
    write_csv(
        dest / "core" / "core_providerprofile.csv",
        list(provider_profiles_out[0].keys()),
        provider_profiles_out,
    )
    user_to_provider_profile = {int(r["user_id"]): int(r["id"]) for r in provider_profiles_out}
    default_provider_profile_id = int(provider_profiles_out[0]["id"]) if provider_profiles_out else 1

    def provider_profile_id(user_ref: str) -> str:
        mapped = user_to_provider_profile.get(int(user_ref))
        return str(mapped if mapped is not None else default_provider_profile_id)

    services_out = []
    for row in read_csv(src / "core_service.csv"):
        price = row.get("price", "0")
        services_out.append(
            {
                "id": row["id"],
                "name": row["name"],
                "slug": slugify(row["name"]) + f"-{row['id']}",
                "description": row.get("description", ""),
                "min_price": price,
                "max_price": price,
                "is_active": "True" if row.get("status", "").lower() == "activ" else "False",
                "created_at": row.get("created_at", "2024-01-01 00:00:00"),
                "updated_at": row.get("created_at", "2024-01-01 00:00:00"),
            }
        )
    write_csv(dest / "core" / "core_service.csv", list(services_out[0].keys()), services_out)

    service_providers_out = []
    for row in read_csv(src / "core_serviceprovider.csv"):
        provider_profile_id_val = provider_profile_id(row["provider_id"])
        service_providers_out.append(
            {
                "id": row["id"],
                "provider_id": provider_profile_id_val,
                "service_id": row["service_id"],
                "duration_minutes": "60",
                "provider_price": "0",
                "created_at": "2024-01-01 00:00:00",
                "updated_at": "2024-01-01 00:00:00",
            }
        )
    write_csv(
        dest / "core" / "core_serviceprovider.csv",
        list(service_providers_out[0].keys()),
        service_providers_out,
    )

    user_reviews_out = []
    for row in read_csv(src / "core_userreview.csv"):
        reviewed_user = int(row["reviewed_user_id"])
        provider_profile_id_val = provider_profile_id(str(reviewed_user))
        rating = max(1, min(10, int(float(row["rating"]))))
        user_reviews_out.append(
            {
                "id": row["id"],
                "reviewer_id": row["reviewer_id"],
                "provider_id": provider_profile_id_val,
                "rating": str(rating),
                "comment": row.get("comment", ""),
                "created_at": row.get("created_at", "2024-01-01 00:00:00"),
                "updated_at": row.get("created_at", "2024-01-01 00:00:00"),
                "booking_id": "",
            }
        )
    write_csv(
        dest / "core" / "core_userreview.csv",
        ["id", "reviewer_id", "provider_id", "rating", "comment", "created_at", "updated_at", "booking_id"],
        user_reviews_out,
    )

    provider_reviews_out = []
    for row in read_csv(src / "core_providerreview.csv"):
        rating = max(1, min(10, int(float(row["rating"]))))
        provider_reviews_out.append(
            {
                "id": row["id"],
                "reviewer_id": row["reviewer_id"],
                "customer_id": row["provider_id"],
                "rating": str(rating),
                "comment": row.get("comment", ""),
                "created_at": row.get("created_at", "2024-01-01 00:00:00"),
                "updated_at": row.get("created_at", "2024-01-01 00:00:00"),
                "booking_id": "",
            }
        )
    write_csv(
        dest / "core" / "core_providerreview.csv",
        list(provider_reviews_out[0].keys()),
        provider_reviews_out,
    )

    availability_rules_out = []
    for row in read_csv(src / "availability_rule.csv"):
        provider_profile_id_val = provider_profile_id(row["provider_id"])
        availability_rules_out.append(
            {
                "id": row["id"],
                "provider_id": provider_profile_id_val,
                "weekday": "0",
                "start_time": "09:00:00",
                "end_time": "17:00:00",
                "timezone": "Europe/Bucharest",
                "is_active": "True" if row.get("rule_type", "").lower() == "disponibil" else "False",
                "valid_from": row.get("start_date", "")[:10],
                "valid_until": row.get("end_date", "")[:10],
                "created_at": row.get("start_date", "2024-01-01 00:00:00"),
                "updated_at": row.get("end_date", "2024-01-01 00:00:00"),
            }
        )
    write_csv(
        dest / "availability" / "availability_rule.csv",
        list(availability_rules_out[0].keys()),
        availability_rules_out,
    )

    availability_customers_out = []
    for row in read_csv(src / "availability_customers.csv"):
        base = row.get("created_at") or "2024-06-01 00:00:00"
        availability_customers_out.append(
            {
                "id": row["id"],
                "customer_id": row["user_id"],
                "starts_at": base,
                "ends_at": base,
                "notes": f"{row.get('day_of_week', '')} {row.get('start_time', '')}-{row.get('end_time', '')}",
                "created_at": base,
                "updated_at": base,
            }
        )
    write_csv(
        dest / "availability" / "availability_customers.csv",
        list(availability_customers_out[0].keys()),
        availability_customers_out,
    )

    availability_providers_out = []
    for row in read_csv(src / "availability_providers.csv"):
        provider_profile_id_val = provider_profile_id(row["provider_id"])
        day = WEEKDAY_MAP.get(row.get("day_of_week", "").lower(), 0)
        base_date = date(2024, 6, 3 + day)
        starts = f"{base_date.isoformat()} {row.get('start_time', '09:00:00')}"
        ends = f"{base_date.isoformat()} {row.get('end_time', '17:00:00')}"
        availability_providers_out.append(
            {
                "id": row["id"],
                "provider_id": provider_profile_id_val,
                "service_id": "",
                "rule_id": row["id"],
                "starts_at": starts,
                "ends_at": ends,
                "status": "open" if row.get("is_available", "").lower() == "true" else "blocked",
                "created_at": starts,
                "updated_at": ends,
            }
        )
    write_csv(
        dest / "availability" / "availability_providers.csv",
        list(availability_providers_out[0].keys()),
        availability_providers_out,
    )

    bookings_out = []
    for row in read_csv(src / "fact_bookings.csv"):
        booking_date = row.get("booking_date", "2024-01-01 00:00:00")
        duration = int(float(row.get("duration_minutes") or 60))
        provider_profile_id_val = provider_profile_id(row["provider_id"])
        status = BOOKING_STATUS.get(row.get("status", "").lower(), "pending")
        client_id = int(row["client_id"])
        bookings_out.append(
            {
                "id": row["id"],
                "customer_id": row["client_id"],
                "provider_id": provider_profile_id_val,
                "service_id": row["service_id"],
                "starts_at": booking_date,
                "ends_at": booking_ends_at(booking_date, duration),
                "duration_minutes": str(duration),
                "price": row.get("total_price", "0"),
                "price_min": row.get("total_price", "0"),
                "price_max": row.get("total_price", "0"),
                "travel_km": "0",
                "travel_time_minutes": "0",
                "status": status,
                "notes": row.get("booking_channel", ""),
                "created_at": row.get("created_at", booking_date),
                "updated_at": row.get("created_at", booking_date),
                "confirmed_at": "",
                "completed_at": "",
                "cancelled_at": "",
                "customer_availability_id": "",
                "provider_availability_id": "",
                "service_link_id": "",
                "visit_location_id": user_home_location.get(client_id, geolocation_for_user(client_id)),
            }
        )
    write_csv(dest / "fact" / "fact_bookings.csv", list(bookings_out[0].keys()), bookings_out)

    payments_out = []
    for row in read_csv(src / "fact_payments.csv"):
        paid_at = row.get("paid_at", "")
        status = PAYMENT_STATUS.get(row.get("status", "").lower(), "pending")
        payments_out.append(
            {
                "id": row["id"],
                "booking_id": row["booking_id"],
                "invoice_id": row["booking_id"],
                "amount": row.get("amount", "0"),
                "currency": row.get("currency", "RON"),
                "payment_method": payment_method(row.get("payment_method", "")),
                "status": status,
                "external_reference": row.get("transaction_id", ""),
                "paid_at": paid_at,
                "created_at": paid_at or "2024-01-01 00:00:00",
                "updated_at": paid_at or "2024-01-01 00:00:00",
            }
        )
    write_csv(dest / "fact" / "fact_payments.csv", list(payments_out[0].keys()), payments_out)

    invoices_out = []
    for row in read_csv(src / "invoices.csv"):
        amount = float(row.get("amount") or 0)
        vat = float(row.get("vat") or 0)
        status = INVOICE_STATUS.get(row.get("status", "").lower(), "issued")
        provider_profile_id_val = provider_profile_id(row["provider_id"])
        invoices_out.append(
            {
                "id": row["id"],
                "invoice_number": row.get("invoice_number", f"INV-{row['id']}"),
                "booking_id": row["id"],
                "customer_id": row["client_id"],
                "provider_id": provider_profile_id_val,
                "subtotal": str(round(amount - vat, 2)),
                "tax": str(vat),
                "total": str(amount),
                "currency": row.get("currency", "RON"),
                "status": status,
                "issued_at": row.get("issued_at", ""),
                "due_at": row.get("due_date", ""),
                "paid_at": "",
                "created_at": row.get("issued_at", "2024-01-01 00:00:00"),
                "updated_at": row.get("issued_at", "2024-01-01 00:00:00"),
            }
        )
    write_csv(dest / "fact" / "invoices.csv", list(invoices_out[0].keys()), invoices_out)

    write_csv(dest / "auth" / "auth_group.csv", ["id", "name"], read_csv(src / "auth_group.csv"))

    group_permissions_out = []
    seen: set[tuple[str, str]] = set()
    for row in read_csv(src / "auth_group_permissions.csv"):
        codename = perm_by_id.get(row["permission_id"], "")
        mapped = PERM_CSV_TO_DJANGO.get(codename)
        if not mapped:
            continue
        app, model, django_codename = mapped
        key = (row["group_id"], django_codename)
        if key in seen:
            continue
        seen.add(key)
        group_permissions_out.append(
            {
                "group_id": row["group_id"],
                "permission_codename": django_codename,
                "content_type_app": app,
                "content_type_model": model,
            }
        )
    write_csv(
        dest / "auth" / "auth_group_permissions.csv",
        ["group_id", "permission_codename", "content_type_app", "content_type_model"],
        group_permissions_out,
    )

    perm_ref_out = []
    for row in read_csv(src / "auth_permission.csv"):
        mapped = PERM_CSV_TO_DJANGO.get(row["codename"])
        perm_ref_out.append(
            {
                "id": row["id"],
                "codename_csv": row["codename"],
                "name": row.get("name", ""),
                "django_codename": mapped[2] if mapped else "",
                "django_app": mapped[0] if mapped else "",
                "django_model": mapped[1] if mapped else "",
            }
        )
    write_csv(
        dest / "auth" / "auth_permission.csv",
        ["id", "codename_csv", "name", "django_codename", "django_app", "django_model"],
        perm_ref_out,
    )

    write_csv(dest / "accounts" / "accounts_user_groups.csv", ["id", "user_id", "group_id"], read_csv(src / "accounts_user_groups.csv"))

    user_permissions_out = []
    seen_up: set[tuple[str, str]] = set()
    for row in read_csv(src / "accounts_user_user_permissions.csv"):
        codename = perm_by_id.get(row["permission_id"], "")
        mapped = PERM_CSV_TO_DJANGO.get(codename)
        if not mapped:
            continue
        app, model, django_codename = mapped
        key = (row["user_id"], django_codename)
        if key in seen_up:
            continue
        seen_up.add(key)
        user_permissions_out.append(
            {
                "id": row["id"],
                "user_id": row["user_id"],
                "permission_codename": django_codename,
                "content_type_app": app,
                "content_type_model": model,
            }
        )
    write_csv(
        dest / "accounts" / "accounts_user_user_permissions.csv",
        ["id", "user_id", "permission_codename", "content_type_app", "content_type_model"],
        user_permissions_out,
    )

    user_languages_out = []
    seen_user_lang: set[tuple[int, int]] = set()
    for row in read_csv(src / "accounts_user_languages.csv"):
        lang_id = lang_name_to_id.get(row.get("language", "").lower())
        if not lang_id:
            continue
        uid = int(row["user_id"])
        key = (uid, lang_id)
        if key in seen_user_lang:
            continue
        seen_user_lang.add(key)
        user_languages_out.append(
            {"id": row["id"], "user_id": row["user_id"], "language_id": str(lang_id)}
        )
    write_csv(
        dest / "accounts" / "accounts_user_languages.csv",
        ["id", "user_id", "language_id"],
        user_languages_out,
    )

    for folder, name in [
        ("django", "django_admin_log.csv"),
        ("django", "django_content_type.csv"),
        ("django", "django_migrations.csv"),
        ("django", "django_session.csv"),
        ("token_blacklist", "token_blacklist_outstandingtoken.csv"),
    ]:
        rows = read_csv(src / name)
        if rows:
            write_csv(dest / folder / name, list(rows[0].keys()), rows)

    bl_rows = read_csv(src / "token_blacklist_blacklistedtoken.csv")
    bl_out = []
    seen_tokens: set[str] = set()
    for row in bl_rows:
        token_ref = row.get("token_id") or row.get("outstanding_token_id")
        if not token_ref or token_ref in seen_tokens:
            continue
        seen_tokens.add(token_ref)
        bl_out.append(
            {
                "id": row["id"],
                "outstanding_token_id": token_ref,
                "blacklisted_at": row.get("blacklisted_at", ""),
            }
        )
    write_csv(
        dest / "token_blacklist" / "token_blacklist_blacklistedtoken.csv",
        ["id", "outstanding_token_id", "blacklisted_at"],
        bl_out,
    )

    print(f"Wrote seed CSVs to {dest}")


if __name__ == "__main__":
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SRC
    build(source, DB_ROOT)
