# Generated by Django 4.2.11 on 2024-07-01 03:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0013_weeklygoal"),
    ]

    operations = [
        migrations.AddField(
            model_name="device",
            name="device_model",
            field=models.CharField(
                blank=True,
                help_text='''Unique identifier for the device\'s model.\n
                getDeviceid() - Gets the device ID.
                iOS: "iPhone7,2"
                Android: "goldfish"
                Windows: "Y3R94UC#AC4"''',
                max_length=25,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="device",
            name="manufacturer",
            field=models.CharField(
                blank=True,
                help_text="""Manufacturer of the device.\n
                getManufacturer() - Gets the device manufacturer
                iOS: "Apple"
                Android: "Google"
                Windows: ?""",
                max_length=25,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="device",
            name="os_name",
            field=models.CharField(
                blank=True,
                help_text="""Operating system of the device.\n
                getSystemName() - Gets the device OS name.
                iOS: "iOS" on newer iOS devices "iPhone OS" on older devices (including older iPad models),
                \t\t"iPadOS" for iPads using iPadOS 15.0 or higher.
                Android: "Android"
                Windows: ?""",
                max_length=25,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="device",
            name="os_version",
            field=models.CharField(
                blank=True,
                help_text="""Device operating system version.\n
                getSystemVersion() - Gets the device OS version.
                iOS: "11.0"
                Android: "7.1.1"
                Windows: ?""",
                max_length=25,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="account",
            name="gender",
            field=models.CharField(
                blank=True,
                choices=[
                    ("CF", "CF"),
                    ("CM", "CM"),
                    ("TF", "TF"),
                    ("TM", "TM"),
                    ("NB", "NB"),
                    ("OT", "OT"),
                    ("DA", "DA"),
                ],
                help_text="Self-identified gender identity of user",
                max_length=2,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="account",
            name="is_latino",
            field=models.CharField(
                blank=True,
                choices=[("YE", "YE"), ("NO", "NO"), ("DA", "DA")],
                help_text="Latino or Hispanic origin",
                max_length=2,
                null=True,
            ),
        ),
        migrations.RemoveField(
            model_name="account",
            name="race",
        ),
        migrations.AddField(
            model_name="account",
            name="race",
            field=models.JSONField(
                blank=True,
                choices=[
                    ("NA", "NA"),
                    ("BL", "BL"),
                    ("AS", "AS"),
                    ("PI", "PI"),
                    ("WH", "WH"),
                    ("OT", "OT"),
                    ("DA", "DA"),
                ],
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="account",
            name="sexual_orien",
            field=models.CharField(
                blank=True,
                choices=[
                    ("BS", "BS"),
                    ("SG", "SG"),
                    ("US", "US"),
                    ("HS", "HS"),
                    ("OT", "OT"),
                    ("DA", "DA"),
                ],
                help_text="Self-identified sexual orientation of user",
                max_length=2,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="account",
            name="zip",
            field=models.CharField(help_text="User's zip code", max_length=25),
        ),
    ]
