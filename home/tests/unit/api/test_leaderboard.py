from datetime import date, datetime, timedelta

from django.test import Client, TestCase
from home.models import Contest
from home.utils import localize
from home.utils.generators import (
    AccountGenerator,
    DailyWalkGenerator,
    DeviceGenerator,
    IntentionalWalkGenerator,
)
from home.views.web.user import (
    get_daily_walk_summaries,
    get_intentional_walk_summaries,
)
from pytz import utc

class TestLeaderboard(TestCase):

    def test_UserListViewEmptyContest_user_counts(self):
        client = Client()
        response = client.get(
            "/api/leaderboard/get" #, {"contest_id": self.contest.contest_id}
        )

        # self.assertEqual(response.context_data["cnt_signups"], 0)
   