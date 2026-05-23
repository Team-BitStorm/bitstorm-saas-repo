from django.db import migrations


def _replace_fk_cascade(cursor, table, column, ref_table, new_constraint_name):
    cursor.execute(
        """
        SELECT tc.constraint_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
         AND tc.table_schema = kcu.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_name = %s
          AND kcu.column_name = %s
        """,
        [table, column],
    )
    row = cursor.fetchone()
    if row:
        cursor.execute(f'ALTER TABLE {table} DROP CONSTRAINT "{row[0]}"')

    cursor.execute(
        f"""
        ALTER TABLE {table}
        ADD CONSTRAINT {new_constraint_name}
        FOREIGN KEY ({column}) REFERENCES {ref_table}(id) ON DELETE CASCADE
        """
    )


def set_blacklistedtoken_cascade(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    with schema_editor.connection.cursor() as cursor:
        _replace_fk_cascade(
            cursor,
            "token_blacklist_blacklistedtoken",
            "token_id",
            "token_blacklist_outstandingtoken",
            "token_blacklist_blacklistedtoken_token_id_cascade_fk",
        )


def unset_blacklistedtoken_cascade(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            ALTER TABLE token_blacklist_blacklistedtoken
            DROP CONSTRAINT IF EXISTS token_blacklist_blacklistedtoken_token_id_cascade_fk
            """
        )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0008_outstandingtoken_user_cascade"),
    ]

    operations = [
        migrations.RunPython(
            set_blacklistedtoken_cascade,
            unset_blacklistedtoken_cascade,
        ),
    ]
