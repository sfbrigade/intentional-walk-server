from datetime import datetime
import json
import requests
from home.models import Device


def make_leadeboard():
    try:  # Is this a valid try/except case
        devices = Device.objects.values("device_id")
        for device in devices:
            # devices = Device.objects.values("device_id").order_by("?").first()
            print("td", device)
            post_data = {
                "account_id": device["device_id"],
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
