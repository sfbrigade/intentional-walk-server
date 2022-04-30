import random

from datetime import date, timedelta
from django.utils import timezone
from enum import Enum
from faker import Faker
from typing import List, Optional
from uuid import uuid4

from home.models import Account, Contest, DailyWalk, Device, IntentionalWalk
from home.models.account import GenderLabels, IsLatinoLabels, RaceLabels, SAN_FRANCISCO_ZIP_CODES, SexualOrientationLabels


class AccountGenerator:
    def __init__(self):
        self.fake = Faker()
        self.zips = list(SAN_FRANCISCO_ZIP_CODES)
        self.genders = list(GenderLabels)
        self.races = list(RaceLabels)
        self.sexual_oriens = list(SexualOrientationLabels)
        self.ethnicity = list(IsLatinoLabels)

    def generate(self, n: int, **kwargs):
        for _ in range(n):
            params = self.random_params()
            params.update(**kwargs)
            yield Account.objects.create(**params)

    def random_params(self):
        # Create racial background with 1-3 races identified
        racial_background = set()
        num_races = random.randint(1, 3)
        for x in range(num_races):
            racial_background.add(random.choice(
                [enm.name for enm in self.races]))
        if "DA" in racial_background:
            racial_background = {'DA'}
        gender_background = random.choice([en.name for en in self.genders])
        return dict(
            email=self.fake.unique.email(),
            name=self.fake.name(),
            # zip=self.fake["en-US"].postcode(),
            zip=random.choice(self.zips),
            age=random.randint(10, 100),
            gender=gender_background,
            gender_other='Gender Queer' if gender_background == 'OT' else None,
            race=racial_background,
            race_other='Middle Eastern' if "OT" in racial_background else None,
            sexual_orien=random.choice([en.name for en in self.sexual_oriens]),
            is_latino=random.choice([en.name for en in self.ethnicity]),
        )


class DeviceGenerator:
    def __init__(self, accounts: Optional[List[Account]] = None):
        self.accounts = accounts

    def generate(self, n: int, **kwargs):
        if not self.accounts and "account" not in kwargs:
            raise InputError("Must provide an Account object as `account`")

        for _ in range(n):
            params = {**self.random_params(), **kwargs}
            yield Device.objects.create(**params)

    def random_params(self):
        values = dict(
            device_id=uuid4(),
        )
        if self.accounts:
            values["account"] = random.choice(self.accounts)
        return values


class DailyWalkGenerator:
    # Requires a list of device ids
    def __init__(self, devices: List[str]):
        self.fake = Faker()
        self.devices = devices

    def generate(self, n: int, **kwargs):
        if not self.devices and "device" not in kwargs:
            raise InputError("Must provide a Device object as `device`")

        for _ in range(n):
            params = {**self.random_params(), **kwargs}
            yield DailyWalk.objects.create(**params)

    def random_params(self):
        values = dict(
            date=self.fake.date(),
            steps=random.randint(100, 10000),
            distance=random.randint(100, 10000),  # up to 10 km
        )
        if self.devices:
            values["device"] = random.choice(self.devices)
        return values


class IntentionalWalkGenerator:
    # Requires a list of device ids
    def __init__(self, devices: List[str]):
        self.fake = Faker()
        if not devices:
            raise InputError("Must provide a non-empty list of device ids")
        self.devices = devices

    def generate(self, n: int, **kwargs):
        for _ in range(n):
            params = {**self.random_params(), **kwargs}
            yield IntentionalWalk.objects.create(**params)

    def random_params(self):
        tz = timezone.get_default_timezone()

        values = dict(
            event_id="event_" + str(self.fake.unique.random_int()),
            start=tz.localize(self.fake.date_time()),
            end=tz.localize(self.fake.date_time()),
            steps=random.randint(10, 10000),
            pause_time=random.randint(10, 3600),  # up to 1 hour
            distance=random.randint(100, 10000),  # up to 10 km
        )
        if self.devices:
            values["device"] = random.choice(self.devices)
        return values


class ContestGenerator:
    def __init__(self):
        self.fake = Faker()

    def generate(self, n: int, **kwargs):
        for _ in range(n):
            params = self.random_params()
            params.update(**kwargs)
            yield Contest.objects.create(**params)

    def random_params(self, start=None, **kwargs):
        if start is None:
            start = date.fromisoformat(self.fake.date())

        return dict(
            start_promo=(start - timedelta(days=7)),
            start=start,
            end=(start + timedelta(days=30)),
        )
