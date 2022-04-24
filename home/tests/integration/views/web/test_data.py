import csv
import io

from collections import defaultdict
from datetime import date, datetime, timedelta
from freezegun import freeze_time
from pytz import utc
from typing import Dict, List

from django.contrib.auth.models import User
from django.test import Client, TestCase

from home.utils.generators import (
    AccountGenerator,
    ContestGenerator,
    DailyWalkGenerator,
    DeviceGenerator,
    IntentionalWalkGenerator,
)
from home.views.web.data import USER_AGG_CSV_BASE_HEADER


class Login:
    username = "testadmin"
    password = "test*PW"

    def __init__(self):
        User.objects.create_user(
            username=self.username, password=self.password)


class TestCsvViews(TestCase):
    @staticmethod
    def login(client: Client):
        return client.login(username=Login.username, password=Login.password)

    @classmethod
    def setUpTestData(cls):
        # Create user login
        Login()

        # Generate fake accounts
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
            t = utc.localize(datetime(3000, 3, 2, 10, 0)) + timedelta(days=(dt * 2))
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

    def test_user_agg_csv_view(self):
        c = Client()
        self.assertTrue(self.login(c))

        with freeze_time("3000-03-02"):
            acct_params = {
                "email": "custom@gmail.com",
                "race": ["BL", "OT"],
                "race_other": "Arab",
                "gender": "OT",
                "gender_other": "Gender Queer",
                "sexual_orien": "OT",
                "sexual_orien_other": "Pansexual",
            }
            new_signup_without_walks = next(AccountGenerator().generate(1, **acct_params))

        params = {
            "start_baseline": date(3000, 2, 28),
            "start_promo": date(3000, 3, 1),
            "start": date(3000, 3, 7),
            "end": date(3000, 3, 14),
        }
        contest_id = next(ContestGenerator().generate(1, **params)).pk

        response = c.get(
            "/data/users_agg.csv",
            {
                "contest_id": contest_id,
            },
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual("text/csv", response["Content-Type"])
        content = response.content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))

        headers = reader.fieldnames
        expected_headers = USER_AGG_CSV_BASE_HEADER[:] + [str(date(3000, 2, 28) + timedelta(days=dt))
                                                          for dt in range(15)]
        self.assertEquals(headers, expected_headers)

        rows = list(reader)
        import pytest
        self.assertEqual(3, len(rows))

        rows_by_email = {r["Email"]: r for r in rows}
        for email, row in rows_by_email.items():
            expected_row = row.copy()

            if email == "custom@gmail.com":
                expected_row.update({
                    "Email": "custom@gmail.com",
                    "Race Other": "Arab",
                    "Gender Identity": "OT",
                    "Gender Identity Other": "Gender Queer",
                    "Sexual Orientation": "OT",
                    "Sexual Orientation Other": "Pansexual",
                    "Is New Signup": "yes",
                    "Active During Contest": "no",
                })
                expected_row.update({k: "" for k in expected_headers[14:]})  # Empty walk data
                self.assertEqual(row, expected_row)
                self.assertIn(row["Race"], {"{'OT', 'BL'}", "{'BL', 'OT'}"})  # order is non-deterministic

            else:
                expected_row.update({
                    "Active During Contest": "yes",
                    "Total Daily Walks During Contest": "4",  # Daily walks on 3-7 through 3-10
                    "Total Daily Walks During Baseline": "6",  # Daily walks on 3-1 through 3-6 (before contest start)
                    "Total Recorded Walks During Contest": "2",  # Intentional walks on 3-8, 3-10
                    "Total Recorded Walks During Baseline": "3",  # Intentional walks on 3-2, 3-4, 3-6
                    "3000-02-28": "",
                    "3000-03-11": "",
                    "3000-03-12": "",
                    "3000-03-13": "",
                    "3000-03-14": "",
                })

                walk_days = [date(3000, 3, 1) + timedelta(days=d) for d in range(10)]  # generated daily walks
                for walk_day in walk_days:
                    self.assertIsNot(row[str(walk_day)], '')  # Some amt of steps on these days in contest/baseline

                for col_name in ["Total Steps During Contest", "Total Steps During Baseline",
                                 "Total Recorded Steps During Contest", "Total Recorded Steps During Baseline",
                                 "Total Recorded Walk Time During Contest", "Total Recorded Walk Time During Baseline"]:
                    self.assertIsNot(row[col_name], '')  # Should be populated from generated dw/iw data

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
                self.assertGreaterEqual(
                    date.fromisoformat(walk["date"]), start_date)
                self.assertLessEqual(
                    date.fromisoformat(walk["date"]), end_date)

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
