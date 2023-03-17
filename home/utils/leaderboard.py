import json
import requests
from home.models import Device


class LeaderboardGenerator:
    def generate(self):
        # datetime.today().strftime('%Y-%m-%d'),
        for x in range(30):
            testd = Device.objects.values("device_id").order_by("?").first()
            post_data = {
                "account_id": testd["device_id"],
                "daily_walks": [
                    {"date": "2023-03-15", "steps": 0, "distance": 0}
                ],
            }

            response = requests.post(
                "http://localhost:8000/api/dailywalk/create",
                data=json.dumps(post_data),
            )
            print(response.content)
