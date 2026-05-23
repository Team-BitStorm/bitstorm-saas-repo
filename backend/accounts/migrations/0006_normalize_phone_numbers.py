from django.db import migrations


def _normalize_phone(value: str) -> str:
    if not value:
        return ""
    return "".join(str(value).split())


def normalize_existing_phones(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    for user in User.objects.exclude(phone_number="").iterator():
        normalized = _normalize_phone(user.phone_number)
        if normalized != user.phone_number:
            user.phone_number = normalized
            user.save(update_fields=["phone_number"])


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0005_remove_user_two_factor_method_user_sms_2fa_enabled"),
    ]

    operations = [
        migrations.RunPython(normalize_existing_phones, migrations.RunPython.noop),
    ]
