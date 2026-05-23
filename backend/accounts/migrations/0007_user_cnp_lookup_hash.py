from django.db import migrations, models


def backfill_cnp_hashes(apps, schema_editor):
    from accounts.cnp_utils import compute_cnp_hash
    from accounts.models import User

    for user in User.objects.exclude(social_security_number="").iterator():
        h = compute_cnp_hash(user.social_security_number)
        if user.cnp_lookup_hash != h:
            User.objects.filter(pk=user.pk).update(cnp_lookup_hash=h)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0006_normalize_phone_numbers"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="cnp_lookup_hash",
            field=models.CharField(blank=True, db_index=True, max_length=64),
        ),
        migrations.RunPython(backfill_cnp_hashes, migrations.RunPython.noop),
    ]
