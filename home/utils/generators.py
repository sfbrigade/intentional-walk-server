import random

from django.utils import timezone
from faker import Faker
from typing import List, Optional
from uuid import uuid4

from home.models import Account, DailyWalk, Device, IntentionalWalk


class AccountGenerator:
    def __init__(self):
        self.fake = Faker()
        self.zips = ['94105', '94107', '94108', '94109', '94112', '94114', '94122', '94124', '94127', '94132', '94131', '94133', '94102', '94103', '94110', '94111', '94115', '94116', '94117', '94118', '94121', '94123', '94134']

    def generate(self, n: int, **kwargs):
        for _ in range(n):
            params = {**self.random_params(), **kwargs}
            yield Account.objects.create(**params)

    def random_params(self):
        return dict(
            email=self.fake.unique.email(),
            name=self.fake.name(),
            # zip=self.fake["en-US"].postcode(),
            zip=random.choice(self.zips),
            age=random.randint(10, 100),
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
