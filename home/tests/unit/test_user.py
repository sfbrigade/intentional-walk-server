from datetime import date, datetime, timedelta
from django.test import Client, TestCase
from pytz import utc

from home.models import Account, Contest, Device, DailyWalk, IntentionalWalk
from home.views.web.user import get_daily_walk_summaries, get_intentional_walk_summaries
from home.utils import localize
from home.utils.generators import (
    AccountGenerator,
    DailyWalkGenerator,
    DeviceGenerator,
    IntentionalWalkGenerator,
)


class TestUserListView(TestCase):
    def setUp(self):
        plum = next(
            AccountGenerator().generate(
                1,
                email="plum@clue.net",
                name="Professor Plum",
            )
        )
        mustard = next(
            AccountGenerator().generate(
                1,
                email="mustard@clue.net",
                name="Colonel Mustard",
            )
        )
        # Device associated with Plum
        device_plum = next(DeviceGenerator([plum]).generate(1))
        # Device associated with Mustard
        device_mustard = next(DeviceGenerator([mustard]).generate(1))

        # Generate daily walks (10 per device)
        dw_plum = DailyWalkGenerator([device_plum])
        dw_mustard = DailyWalkGenerator([device_mustard])
        for dt in range(20):
            # Set dates on walks to 3000-03-01 to 3000-03-20
            t = utc.localize(datetime(3000, 3, 1, 10, 0)) + timedelta(days=dt)
            next(dw_plum.generate(1, date=t, steps=100, distance=50))
            next(dw_mustard.generate(1, date=t, steps=200, distance=100))

        # Generate intentional walks (5, every other day)
        iw_plum = IntentionalWalkGenerator([device_plum])
        iw_mustard = IntentionalWalkGenerator([device_mustard])
        for dt in range(10):
            # Set dates on walks to [2, 4, 6, 8, 10, 12, 14, 16, 18, 20] (3000-03)
            t = utc.localize(datetime(3000, 3, 2, 10, 0)) + timedelta(days=(dt * 2))
            next(iw_plum.generate(1, steps=10, start=t, end=(t + timedelta(hours=1))))
            next(
                iw_mustard.generate(1, steps=20, start=t, end=(t + timedelta(hours=2)))
            )

        self.contest = Contest.objects.create(
            start_promo="3000-03-01",
            start="3000-03-08",
            end="3000-03-14",
        )

    def test_get_daily_walk_summaries(self):
        # Get one week's worth of data (3/1 to 3/7 inclusive)
        dw = get_daily_walk_summaries(date__range=(date(3000, 3, 1), date(3000, 3, 14)))

        plum_data = dw["plum@clue.net"]
        self.assertEqual(14, plum_data["dw_count"])
        self.assertEqual(1400, plum_data["dw_steps"])
        self.assertEqual(700, plum_data["dw_distance"])

        mustard_data = dw["mustard@clue.net"]
        self.assertEqual(14, mustard_data["dw_count"])
        self.assertEqual(2800, mustard_data["dw_steps"])
        self.assertEqual(1400, mustard_data["dw_distance"])

    def test_get_intentional_walk_summaries(self):
        iw = get_intentional_walk_summaries(
            start__range=(
                localize(date(3000, 3, 1)),
                localize(date(3000, 3, 14)) + timedelta(days=1),
            )
        )

        plum_data = iw["plum@clue.net"]
        # 7 intentional walks during this period: 2, 4, 6, 8, 10, 12, 14
        self.assertEqual(7, plum_data["rw_count"])
        # 1 hour per walk
        self.assertEqual(7 * 3600, plum_data["rw_total_walk_time"].total_seconds())
        # 10 steps per walk
        self.assertEqual(70, plum_data["rw_steps"])

        mustard_data = iw["mustard@clue.net"]
        self.assertEqual(7, mustard_data["rw_count"])
        self.assertEqual(14 * 3600, mustard_data["rw_total_walk_time"].total_seconds())
        self.assertEqual(140, mustard_data["rw_steps"])

    def test_UserListView_all_walks(self):
        client = Client()
        response = client.get("/users/")
        user_stats_list = response.context_data["user_stats_list"]
        self.assertEqual(2, len(user_stats_list))
        user_stats = {row["account"]["email"]: row for row in user_stats_list}
        plum_data = user_stats["plum@clue.net"]
        mustard_data = user_stats["mustard@clue.net"]
        self.assertEqual(20, plum_data["num_dws"])
        self.assertEqual(20, mustard_data["num_dws"])
        self.assertEqual(10, plum_data["num_rws"])
        self.assertEqual(10, mustard_data["num_rws"])

    def test_UserListView_with_contest_id(self):
        client = Client()
        response = client.get("/users/", {"contest_id": self.contest.contest_id})
        user_stats_list = response.context_data["user_stats_list"]
        self.assertEqual(2, len(user_stats_list))
        user_stats = {row["account"]["email"]: row for row in user_stats_list}
        plum_data = user_stats["plum@clue.net"]
        mustard_data = user_stats["mustard@clue.net"]
        # dw: [8, 9. 10, 11, 12, 13, 14]
        self.assertEqual(7, plum_data["num_dws"])
        self.assertEqual(7, mustard_data["num_dws"])
        # iw: [8, 10, 12, 14]
        self.assertEqual(4, plum_data["num_rws"])
        self.assertEqual(4, mustard_data["num_rws"])
