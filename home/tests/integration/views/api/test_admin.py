import math

from datetime import date, datetime, timedelta

from django.contrib.auth.models import User
from django.test import Client, TestCase
from freezegun import freeze_time

from home.utils.generators import (
    AccountGenerator,
    ContestGenerator,
    DailyWalkGenerator,
    DeviceGenerator,
    IntentionalWalkGenerator,
)
from pytz import utc


class Login:
    username = "testadmin"
    password = "test*PW"

    def __init__(self):
        User.objects.create_user(
            username=self.username, password=self.password
        )


class TestAdminViews(TestCase):
    contest0_id = None

    @staticmethod
    def login(client: Client):
        return client.login(username=Login.username, password=Login.password)

    @classmethod
    def setUpTestData(cls):
        # Create user login
        Login()

        # Accounts generated for testing
        # account0: 94102 signup before current contest, not part of current contest
        # account1: 94102 signup before current contest, tester, dailywalks 5k steps/day, intentionalwalks
        # account2: 94103 signup before current contest, dailywalks 10k steps/day, intentionalwalks
        # account3: 94103 signup during current contest, dailywalks 15k steps/day
        # account4: 94104 signup during current contest, intentionalwalks
        # account5: 94104 signup during current contest, inactive

        # Generate 3 accounts before the current contest
        accounts = list(AccountGenerator().generate(3))
        # Make second account a tester
        accounts[1].is_tester = True
        accounts[1].save()
        # Generate 3 accounts during the contest
        with freeze_time("3000-03-02"):
            accounts = accounts + list(AccountGenerator().generate(3))
        # Set names for testing ordering, zip codes for grouping
        for i, account in enumerate(accounts):
            account.name = f"User {i}"
            account.zip = f"{94102 + math.floor(i / 2)}"
            account.save()

        # generate devices for the active accounts
        device1 = list(DeviceGenerator(accounts[1:2]).generate(1))
        device2 = list(DeviceGenerator(accounts[2:3]).generate(1))
        device3 = list(DeviceGenerator(accounts[3:4]).generate(1))
        device4 = list(DeviceGenerator(accounts[4:5]).generate(1))

        # Generate the "current" Contest we want to test with
        params = {
            "start_baseline": date(3000, 2, 28),
            "start_promo": date(3000, 3, 1),
            "start": date(3000, 3, 7),
            "end": date(3000, 3, 14),
        }
        contest0 = next(ContestGenerator().generate(1, **params))
        # save its id in a class variable for use in tests
        cls.contest0_id = str(contest0.pk)

        # Add the last five accounts to this contest
        for account in accounts[1:6]:
            account.contests.add(contest0)

        # Generate daily walks (10 per device)
        dwalks1 = DailyWalkGenerator(device1)
        dwalks2 = DailyWalkGenerator(device2)
        dwalks3 = DailyWalkGenerator(device3)
        for dt in range(14):
            # Set dates on walks to 3000-02-28 to 3000-03-14
            t = utc.localize(datetime(3000, 2, 28, 10, 0)) + timedelta(days=dt)
            next(dwalks1.generate(1, date=t, steps=5000, distance=4000))
            next(dwalks2.generate(1, date=t, steps=10000, distance=8000))
            next(dwalks3.generate(1, date=t, steps=15000, distance=12000))

        # Generate intentional walks (5, every other day)
        iwalks1 = IntentionalWalkGenerator(device1)
        iwalks2 = IntentionalWalkGenerator(device2)
        iwalks4 = IntentionalWalkGenerator(device4)
        for dt in range(5):
            # Set dates on walks to [2, 4, 6, 8, 10] (3000-03)
            t = utc.localize(datetime(3000, 3, 2, 10, 0)) + timedelta(
                days=(dt * 2)
            )
            next(iwalks1.generate(1, start=t, end=(t + timedelta(hours=2))))
            next(iwalks2.generate(1, start=t, end=(t + timedelta(hours=2))))
            next(iwalks4.generate(1, start=t, end=(t + timedelta(hours=2))))

        # create an "old" Contest, make first acccount part of it
        params = {
            "start_baseline": date(2999, 2, 28),
            "start_promo": date(2999, 3, 1),
            "start": date(2999, 3, 7),
            "end": date(2999, 3, 14),
        }
        contest1 = next(ContestGenerator().generate(1, **params))
        accounts[0].contests.add(contest1)

    def test_get_me(self):
        c = Client()
        # when unauthenticated, returns an empty response
        response = c.get("/api/admin/me")
        self.assertEqual(response.status_code, 204)

        # log in
        self.assertTrue(self.login(c))

        # when authenticated, returns the JSON representation of the user
        response = c.get("/api/admin/me")
        data = response.json()
        self.assertEqual(data["username"], "testadmin")

    def test_get_home(self):
        c = Client()
        self.assertTrue(self.login(c))
        response = c.get("/api/admin/home")
        data = response.json()
        self.assertEqual(
            data,
            {
                "accounts_count": 5,  # 6 accounts - 1 tester
                "accounts_steps": 350000,  # 14 days * (10,000 + 15,000 steps/day)
                "accounts_distance": 280000,  # 14 days * (8,000 + 12,000 meters/day)
            },
        )

    def test_get_contests(self):
        c = Client()
        self.assertTrue(self.login(c))
        response = c.get("/api/admin/contests")
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["contest_id"], self.contest0_id)

    def test_get_users(self):
        c = Client()
        self.assertTrue(self.login(c))
        response = c.get("/api/admin/users")
        data = response.json()
        self.assertEqual(len(data), 5)  # 6 accounts - 1 tester

        response = c.get(f"/api/admin/users?contest_id={self.contest0_id}")
        data = response.json()
        self.assertEqual(len(data), 4)  # 5 accounts in the contest - 1 tester
        # default ordering is by name
        self.assertEqual(data[0]["name"], "User 2")
        self.assertEqual(data[0]["is_new"], False)
        self.assertEqual(data[0]["dw_count"], 7)
        self.assertEqual(data[0]["dw_steps"], 70000)
        self.assertEqual(data[0]["dw_distance"], 56000)
        self.assertEqual(data[1]["name"], "User 3")
        self.assertEqual(data[1]["is_new"], True)
        self.assertEqual(data[1]["dw_count"], 7)
        self.assertEqual(data[1]["dw_steps"], 105000)
        self.assertEqual(data[1]["dw_distance"], 84000)
        self.assertEqual(data[2]["name"], "User 4")
        self.assertEqual(data[2]["is_new"], True)
        self.assertEqual(data[2]["dw_count"], 0)
        self.assertEqual(data[2]["dw_steps"], None)
        self.assertEqual(data[2]["dw_distance"], None)
        self.assertEqual(data[3]["name"], "User 5")
        self.assertEqual(data[3]["is_new"], True)
        self.assertEqual(data[3]["dw_count"], 0)
        self.assertEqual(data[3]["dw_steps"], None)
        self.assertEqual(data[3]["dw_distance"], None)

        response = c.get(
            f"/api/admin/users?contest_id={self.contest0_id}&is_tester=true"
        )
        data = response.json()
        self.assertEqual(len(data), 1)  # 1 tester

    def test_get_users_by_zip(self):
        c = Client()
        self.assertTrue(self.login(c))
        response = c.get(f"/api/admin/users/zip?contest_id={self.contest0_id}")
        data = response.json()
        self.assertEqual(
            data,
            {
                "total": {"94103": 2, "94104": 2},
                "new": {"94103": 1, "94104": 2},
            },
        )

    def test_get_users_active_by_zip(self):
        c = Client()
        self.assertTrue(self.login(c))
        response = c.get(
            f"/api/admin/users/zip/active?contest_id={self.contest0_id}"
        )
        data = response.json()
        self.assertEqual(
            data,
            {
                "total": {"94103": 2, "94104": 1},
                "new": {"94103": 1, "94104": 1},
            },
        )

    def test_get_users_median_steps_by_zip(self):
        c = Client()
        self.assertTrue(self.login(c))
        response = c.get(
            f"/api/admin/users/zip/steps?contest_id={self.contest0_id}"
        )
        data = response.json()
        self.assertEqual(
            data,
            {
                "all": 87500.0,
                "94103": 87500.0,
            },  # median of [70k, 105k] = avg of the two = 87.5k
        )
