# Database seed CSV files

CSV exports organized by Django app. Loaded with:

```bash
cd backend
uv run python manage.py migrate
uv run python manage.py load_seed_csv
```

## Layout

| Folder | Files |
|--------|--------|
| `accounts/` | `accounts_user.csv`, `accounts_user_groups.csv`, `accounts_user_user_permissions.csv` |
| `auth/` | `auth_group.csv`, `auth_group_permissions.csv`, `auth_permission.csv` (reference) |
| `django/` | `django_admin_log.csv`, `django_session.csv`, `django_content_type.csv`, `django_migrations.csv` (reference only) |
| `token_blacklist/` | `token_blacklist_outstandingtoken.csv`, `token_blacklist_blacklistedtoken.csv` |

`accounts_user.csv` matches `accounts.User`: no `username`; includes `phone_number`, `birth_date`, `social_security_number`, and `role`.

`django_migrations.csv` and `django_content_type.csv` are kept for reference and are **not** imported (Django manages those via `migrate`).

## Options

- `--clear` — remove seeded rows before loading
- `--password` — set all user passwords (default: `CarePath2026!`)
