import json
import requests
from home.models import Device
from datetime import datetime

try:
    for x in range(30):
            testd = Device.objects.values("device_id").order_by('?').first()
            post_data = {
            "account_id": testd["device_id"],
                "daily_walks": [
                {
            "date": datetime.today().strftime('%Y-%m-%d'),
            "steps": 0,
            "distance": 0
                }]}


            response = requests.post('http://localhost:8000/api/dailywalk/create',
                data=json.dumps(post_data))
            content = response.content
except:
    print("Error creating Leaderboard")