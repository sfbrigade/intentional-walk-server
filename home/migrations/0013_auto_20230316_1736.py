# Generated by Django 3.2.15 on 2023-03-17 00:36

from datetime import datetime
from django.db import migrations

import json
import requests


def GenerateLeaderboard(apps, schema_editor):
    Device = apps.get_model("home", "Device")

    try:  # Is this a valid try/except case
        for x in range(50):
            testd = Device.objects.values("device_id").order_by("?").first()
            print("td", testd)
            post_data = {
                "account_id": testd["device_id"],
                "daily_walks": [
                    {
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "steps": 0,
                        "distance": 0,
                    }
                ],
            }

            response = requests.post(
                "http://localhost:8000/api/dailywalk/create",
                data=json.dumps(post_data),
            )
            print(response.content)
    except Exception:
        print("Error creating leaderbord")


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0012_merge_0011_intentionalwalk_walk_time_0011_leaderboard"),
    ]

    operations = [
        migrations.RunPython(GenerateLeaderboard),
    ]
