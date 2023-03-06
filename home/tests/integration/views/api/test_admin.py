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
        # account0: signup before current contest, not part of current contest
        # account1: signup before current contest, tester, dailywalks, intentionalwalks
        # account2: signup before current contest, dailywalks, intentionalwalks
        # account3: signup during current contest, dailywalks
        # account4: signup during current contest, intentionalwalks
        # account5: signup during current contest, inactive

        # Generate 3 accounts before the current contest
        accounts = list(AccountGenerator().generate(3))
        # Make second account a tester
        accounts[1].is_tester = True
        accounts[1].save()
        # Generate 3 accounts during the contest
        with freeze_time("3000-03-01"):
            accounts = accounts + list(AccountGenerator().generate(3))

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
        cls.contest0_id = contest0.pk

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
