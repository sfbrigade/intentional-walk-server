import csv
import io

from datetime import date, datetime, timedelta
from faker import Faker
from pytz import utc

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
        accounts = list(AccountGenerator().generate(1))
        devices = list(DeviceGenerator(accounts).generate(1))

        # Generate daily walks
        dwalks = list(DailyWalkGenerator(devices).generate(10))
        for dt, obj in zip(range(len(dwalks)), dwalks):
            # Set dates on walks to 3000-03-01 to 3000-03-10
            t = utc.localize(datetime(3000, 3, 1, 10, 0)) + timedelta(days=dt)
            obj.date = t
            obj.save()

        # Generate intentional walks
        iwalks = list(IntentionalWalkGenerator(devices).generate(10))
        for dt, obj in zip(range(len(iwalks)), iwalks):
            # Set dates on walks to 3000-03-01 to 3000-03-10
            t = utc.localize(datetime(3000, 3, 1, 10, 0)) + timedelta(days=dt)
            obj.start = t
            obj.end = t + timedelta(hours=2)
            obj.save()

    @staticmethod
    def date_from_timestamp(ts: str):
        return datetime.fromisoformat(ts).date()

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
        self.assertEqual(2, len(rows))  # includes dummy account
        for row in rows:
            if row["name"] == "Dummy Account":
                self.assertEqual(int(row["total_steps"]), 0)
            else:
                self.assertEqual(int(row["num_daily_walks"]), 4)
                self.assertEqual(int(row["num_recorded_walks"]), 4)

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
        self.assertEqual(4, len(rows))

        for row in rows:
            self.assertGreaterEqual(date.fromisoformat(row["date"]), start_date)
            self.assertLessEqual(date.fromisoformat(row["date"]), end_date)

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
        self.assertEqual(4, len(rows))

        for row in rows:
            self.assertGreaterEqual(
                self.date_from_timestamp(row["start_time"]), start_date
            )
            self.assertLessEqual(self.date_from_timestamp(row["end_time"]), end_date)
