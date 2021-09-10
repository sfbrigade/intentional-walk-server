import csv
import io

from collections import defaultdict
from datetime import date, datetime, timedelta
from faker import Faker
from pytz import utc
from typing import Dict, List

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import Client, TestCase

from home.models import IntentionalWalk
from home.utils.generators import (
    AccountGenerator,
    DailyWalkGenerator,
    DeviceGenerator,
    IntentionalWalkGenerator,
)


class Login:
    username = "testadmin"
    password = "test*PW"

    def __init__(self):
        User.objects.create_user(username=self.username, password=self.password)


def setUpModule():
    Login()


class TestCsvViews(TestCase):
    @staticmethod
    def login(client: Client):
        return client.login(username=Login.username, password=Login.password)

    @classmethod
    def setUpTestData(cls):
        fake = Faker()
        accounts = list(AccountGenerator().generate(2))
        # Device associated with accounts[0]
        device0 = list(DeviceGenerator(accounts[0:1]).generate(1))
        # Device associated with accounts[1]
        device1 = list(DeviceGenerator(accounts[1:2]).generate(1))

        # Generate daily walks (10 per device)
        dwalks0 = DailyWalkGenerator(device0)
        dwalks1 = DailyWalkGenerator(device1)
        for dt in range(10):
            # Set dates on walks to 3000-03-01 to 3000-03-10
            t = utc.localize(datetime(3000, 3, 1, 10, 0)) + timedelta(days=dt)
            next(dwalks0.generate(1, date=t))
            next(dwalks1.generate(1, date=t))

        # Generate intentional walks (5, every other day)
        iwalks0 = IntentionalWalkGenerator(device0)
        iwalks1 = IntentionalWalkGenerator(device1)
        for dt in range(5):
            # Set dates on walks to [2, 4, 6, 8, 10] (3000-03)
            t = utc.localize(datetime(3000, 3, 1, 10, 0)) + timedelta(days=(dt * 2))
            next(iwalks0.generate(1, start=t, end=(t + timedelta(hours=2))))
            next(iwalks1.generate(1, start=t, end=(t + timedelta(hours=2))))

    @staticmethod
    def date_from_timestamp(ts: str) -> datetime.date:
        return datetime.fromisoformat(ts).date()

    @staticmethod
    def group_by(rows: List[Dict], key: str) -> Dict[str, List]:
        grouped = defaultdict(list)
        for row in rows:
            grouped[row[key]].append(row)
        return grouped

    def test_users_agg_csv_view(self):
        c = Client()
        self.assertTrue(self.login(c))
        start_date = date(3000, 3, 7)
        end_date = date(3000, 3, 14)
        response = c.get(
            "/data/users_agg.csv",
            {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual("text/csv", response["Content-Type"])
        content = response.content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
        headers = reader.fieldnames
        self.assertIn("email", headers)
        self.assertIn("total_steps", headers)
        self.assertEqual(3, len(rows))  # includes dummy account
        for row in rows:
            if row["name"] == "Dummy Account":
                self.assertEqual(int(row["total_steps"]), 0)
            else:
                # Daily walks: [7, 8, 9, 10]
                self.assertEqual(int(row["num_daily_walks"]), 4)
                # Intentional walks: [8, 10]
                self.assertEqual(int(row["num_recorded_walks"]), 2)

    # Test csv response of daily walks
    def test_daily_walks_csv_view(self):
        c = Client()
        self.assertTrue(self.login(c))
        start_date = date(3000, 3, 7)
        end_date = date(3000, 3, 14)
        response = c.get(
            "/data/daily_walks.csv",
            {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual("text/csv", response["Content-Type"])
        content = response.content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
        headers = reader.fieldnames
        self.assertIn("date", headers)
        self.assertIn("steps", headers)

        grouped_rows = self.group_by(rows, "email")
        for user, walks in grouped_rows.items():
            self.assertEqual(4, len(walks))  # [7, 8, 9, 10]

            for walk in walks:
                self.assertGreaterEqual(date.fromisoformat(walk["date"]), start_date)
                self.assertLessEqual(date.fromisoformat(walk["date"]), end_date)

    # Test csv response of intentional (recorded) walks
    def test_intentional_walks_csv_view(self):

        c = Client()
        self.assertTrue(self.login(c))
        start_date = date(3000, 3, 7)
        end_date = date(3000, 3, 14)
        response = c.get(
            "/data/intentional_walks.csv",
            {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )

        self.assertEqual("text/csv", response["Content-Type"])
        self.assertEqual(200, response.status_code)
        content = response.content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
        headers = reader.fieldnames
        self.assertIn("event_id", headers)
        self.assertIn("steps", headers)

        grouped_rows = self.group_by(rows, "email")

        for user, walks in grouped_rows.items():
            self.assertEqual(2, len(walks))  # [8, 10]

            for walk in walks:
                self.assertGreaterEqual(
                    self.date_from_timestamp(walk["start_time"]), start_date
                )
                self.assertLessEqual(
                    self.date_from_timestamp(walk["end_time"]), end_date
                )
