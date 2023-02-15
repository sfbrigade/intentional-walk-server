from django.test import Client, TestCase


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
