# Generated by Django 3.2.15 on 2023-08-22 01:39

from django.db import migrations, models
import django.db.models.deletion
import home.utils.dates


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0012_merge_0011_intentionalwalk_walk_time_0011_leaderboard"),
    ]

    operations = [
        migrations.CreateModel(
            name="WeeklyGoal",
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
                (
                    "start_of_week",
                    models.DateField(
                        default=home.utils.dates.get_start_of_current_week,
                        help_text="The start of the week for the goal",
                    ),
                ),
                (
                    "steps",
                    models.IntegerField(help_text="Step goal for the week"),
                ),
                (
                    "days",
                    models.IntegerField(
                        help_text="Number of days per week to reach goal"
                    ),
                ),
                (
                    "account",
                    models.ForeignKey(
                        help_text="Account the data is linked to",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="home.account",
                    ),
                ),
            ],
            options={
                "ordering": ("-start_of_week",),
            },
        ),
    ]
