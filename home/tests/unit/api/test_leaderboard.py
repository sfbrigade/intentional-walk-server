from django.test import Client, TestCase

import json
import requests
from models import Device
from datetime import datetime

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
      

#  real_response = {
#     "account_id": "691d690b-da13-4864-b5ff-4d1535a6528d",
#     "daily_walks": [
#         {"date": "2022-07-25", "steps": 10000, "distance": 5}
#     ],
# }


class TestLeaderboard(TestCase):
    def test_Leaderboard(self):
        client = Client()
        response = client.get(
            "/api/leaderboard/get"
            # , {"contest_id": self.contest.contest_id}
        )
        print(response)
        print("end response)")
        self.assertEqual(response, response)
