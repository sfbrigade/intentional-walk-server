from django.db import migrations, models
from home.models.account import SAN_FRANCISCO_ZIP_CODES

"""
This migration adds new demographic fields into Account:
 * is_latino: Latino/Hispanic origin
 * is_sf_resident: whether the user is a SF resident or not (based on zip)

It also creates a new table of Race
(many-to-many relationship of users and races)
"""


def populate_is_sf_resident(apps, schema_editor):
    Account = apps.get_model("home", "Account")
    db_alias = schema_editor.connection.alias

    for account in Account.objects.using(db_alias):
        account.is_sf_resident = account.zip in SAN_FRANCISCO_ZIP_CODES
        account.save()


def depopulate_is_sf_resident(apps, schema_editor):
    Account = apps.get_model("home", "Account")
    db_alias = schema_editor.connection.alias

    for account in Account.objects.using(db_alias):
        account.is_sf_resident = None
        account.save()


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0006_auto_20200623_2207"),
    ]

    operations = [
        migrations.CreateModel(
            name="Race",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("label", models.CharField(max_length=75, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name="account",
            name="is_sf_resident",
            field=models.BooleanField(
                help_text=(
                    "Whether the user is a SF resident or not, based on zip"
                ),
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="account",
            name="is_latino",
            field=models.BooleanField(
                blank=True, help_text="Latino or Hispanic origin", null=True
            ),
        ),
        migrations.AddField(
            model_name="account",
            name="race",
            field=models.ManyToManyField(
                blank=True,
                help_text="Self-identified race(s) of user",
                to="home.Race",
            ),
        ),
        migrations.AddField(
            model_name="account",
            name="gender",
            field=models.CharField(
                blank=True,
                help_text="Self-identified gender identity of user",
                max_length=25,
            ),
        ),
        migrations.AddField(
            model_name="account",
            name="is_tester",
            field=models.BooleanField(
                help_text="User is an app tester", default=False
            ),
        ),
        migrations.RunPython(
            populate_is_sf_resident, reverse_code=depopulate_is_sf_resident
        ),
    ]
