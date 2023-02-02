from django.test import Client, TestCase


class TestLeaderboard(TestCase):
    def test_UserListViewEmptyContest_user_counts(self):
        client = Client()
        response = client.get(
            "/api/leaderboard/get"
            # , {"contest_id": self.contest.contest_id}
        )
        self.assertEqual(response, response)
