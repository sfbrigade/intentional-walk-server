# Generated by Django 3.0.5 on 2020-04-26 06:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0002_remove_dailywalk_event_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="intentionalwalk",
            name="event_id",
            field=models.CharField(max_length=250, unique=True),
        ),
    ]
