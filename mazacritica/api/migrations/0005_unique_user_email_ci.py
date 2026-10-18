from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_comment_moderationaction_commentreport'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                'CREATE UNIQUE INDEX IF NOT EXISTS unique_user_email_ci '
                "ON auth_user (LOWER(email)) WHERE email <> '';"
            ),
            reverse_sql='DROP INDEX IF EXISTS unique_user_email_ci;',
        ),
    ]
