from django.test import Client, TestCase

#    for x in range(5):
#         num = random.randint(30, 90)
#         testd = Device.objects.values("device_id").order_by('?').first()
#         post_data = {
#         "account_id": testd["device_id"],
#             "daily_walks": [
# 	        {
# 		"date": "2023-03-08",
# 		"steps": num,
# 		"distance": 5
# 	        }]}


#         response = requests.post('http://localhost:8000/api/dailywalk/create',
#              data=json.dumps(post_data))
#         content = response.content
#         #print(response)
#         print(post_data)

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
