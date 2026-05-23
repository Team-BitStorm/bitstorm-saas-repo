# Database seed CSV files (Romanian demo dataset)

CSV exports organized by Django app. Loaded with:

```bash
cd backend
uv run python manage.py migrate
uv run python manage.py load_seed_csv --clear
```

## Dataset

- **150 users** with Romanian names and `@exemplu.ro` emails
- **8 groups**: Administratori, Editori, Vizitatori, Moderatori, Suport, Analiști, Manageri, Contabili
- JWT tokens, admin log entries, and group memberships from the Romanian seed export

`accounts_user.csv` matches `accounts.User`: no `username`; includes `phone_number`, `birth_date`, `social_security_number`, and `role`.

`auth_permission.csv` is a **reference** mapping Romanian permission labels to Django codenames (`add_user`, etc.).

`django_migrations.csv` and `django_content_type.csv` are reference only — Django manages those via `migrate`.

## Options

- `--clear` — remove seeded rows before loading
- `--password` — set all user passwords (default: `CarePath2026!`)
