from django.db import migrations


def set_outstandingtoken_user_cascade(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT tc.constraint_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
             AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_name = 'token_blacklist_outstandingtoken'
              AND kcu.column_name = 'user_id'
            """
        )
        row = cursor.fetchone()
        if row:
            constraint_name = row[0]
            cursor.execute(
                f"ALTER TABLE token_blacklist_outstandingtoken "
                f'DROP CONSTRAINT "{constraint_name}"'
            )

        cursor.execute(
            """
            ALTER TABLE token_blacklist_outstandingtoken
            ADD CONSTRAINT token_blacklist_outstandingtoken_user_id_cascade_fk
            FOREIGN KEY (user_id) REFERENCES accounts_user(id) ON DELETE CASCADE
            """
        )


def unset_outstandingtoken_user_cascade(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            ALTER TABLE token_blacklist_outstandingtoken
            DROP CONSTRAINT IF EXISTS token_blacklist_outstandingtoken_user_id_cascade_fk
            """
        )
        cursor.execute(
            """
            ALTER TABLE token_blacklist_outstandingtoken
            ADD CONSTRAINT token_blacklist_outs_user_id_83bc629a_fk_accounts_
            FOREIGN KEY (user_id) REFERENCES accounts_user(id) ON DELETE SET NULL
            """
        )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0007_user_cnp_lookup_hash"),
        ("token_blacklist", "0013_alter_blacklistedtoken_options_and_more"),
    ]

    operations = [
        migrations.RunPython(
            set_outstandingtoken_user_cascade,
            unset_outstandingtoken_user_cascade,
        ),
    ]
