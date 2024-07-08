import math
from datetime import date, datetime, timedelta

from django.contrib.auth.models import User
from django.test import Client
from django.utils import timezone
from freezegun import freeze_time
from pytz import utc

from home.utils.generators import (
    AccountGenerator,
    ContestGenerator,
    DailyWalkGenerator,
    DeviceGenerator,
    IntentionalWalkGenerator,
)


class Login:
    username = "testadmin"
    password = "test*PW"

    def __init__(self):
        User.objects.create_user(
            username=self.username, password=self.password
        )

    @classmethod
    def login(cls, client: Client):
        return client.login(username=cls.username, password=cls.password)


def generate_test_data():
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
    with freeze_time("3000-03-02 12:00:00"):
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

    # Add the last five accounts to this contest
    for account in accounts[1:6]:
        account.contests.add(contest0)

    # Generate daily walks (10 per device)
    dwalks1 = DailyWalkGenerator(device1)
    dwalks2 = DailyWalkGenerator(device2)
    dwalks3 = DailyWalkGenerator(device3)
    tz = timezone.get_default_timezone()
    for dt in range(14):
        # Set dates on walks to 3000-02-28 to 3000-03-14
        t = datetime(3000, 2, 28, 10, 0).astimezone(tz) + timedelta(days=dt)
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
        next(
            iwalks1.generate(
                1, start=t, end=(t + timedelta(hours=2)), steps=1000
            )
        )
        next(
            iwalks2.generate(
                1, start=t, end=(t + timedelta(hours=2)), steps=2000
            )
        )
        next(
            iwalks4.generate(
                1, start=t, end=(t + timedelta(hours=2)), steps=3000
            )
        )

    # create an "old" Contest, make first acccount part of it
    params = {
        "start_baseline": date(2999, 2, 28),
        "start_promo": date(2999, 3, 1),
        "start": date(2999, 3, 7),
        "end": date(2999, 3, 14),
    }
    contest1 = next(ContestGenerator().generate(1, **params))
    accounts[0].contests.add(contest1)

    # return the "current" contest id
    return str(contest0.pk)
