from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ("home", "0014_account_race_json"),
    ]

    operations = [
        migrations.RunSQL(
            "UPDATE home_account SET race_json = to_jsonb(race);"
        ),
    ]
