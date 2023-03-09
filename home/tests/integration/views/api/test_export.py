import csv
import io
import logging

from datetime import date, timedelta

from django.test import Client, TestCase

from home.views.api.export import CSV_COLUMNS
from .utils import Login, generate_test_data

logger = logging.getLogger(__name__)


class TestExportViews(TestCase):
    contest0_id = None

    @classmethod
    def setUpTestData(cls):
        cls.contest0_id = generate_test_data()

    def test_export_users(self):
        c = Client()
        self.assertTrue(Login.login(c))

        response = c.get(f"/api/export/users?contest_id={self.contest0_id}")
        self.assertEqual(200, response.status_code)
        self.assertEqual("application/octet-stream", response["Content-Type"])

        content = response.getvalue().decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))
        headers = reader.fieldnames
        self.assertEqual(
            headers,
            [col["name"] for col in CSV_COLUMNS]
            + [
                str(date(3000, 2, 28) + timedelta(days=dt)) for dt in range(15)
            ],
        )

        rows = list(reader)
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0]["Participant Name"], "User 2")
        self.assertEqual(rows[0]["Is New Signup"], "False")
        self.assertEqual(rows[0]["Active During Contest"], "True")
        self.assertEqual(rows[0]["Total Daily Walks During Contest"], "7")
        self.assertEqual(rows[0]["Total Steps During Contest"], "70000")
        self.assertEqual(rows[0]["Total Recorded Walks During Contest"], "2")
        self.assertEqual(
            rows[0]["Total Recorded Steps During Contest"], "4000"
        )

        self.assertEqual(rows[1]["Participant Name"], "User 3")
        self.assertEqual(rows[1]["Is New Signup"], "True")
        self.assertEqual(rows[1]["Active During Contest"], "True")
        self.assertEqual(rows[1]["Total Daily Walks During Contest"], "7")
        self.assertEqual(rows[1]["Total Steps During Contest"], "105000")
        self.assertEqual(rows[1]["Total Recorded Walks During Contest"], "0")
        self.assertEqual(rows[1]["Total Recorded Steps During Contest"], "")

        self.assertEqual(rows[2]["Participant Name"], "User 4")
        self.assertEqual(rows[2]["Is New Signup"], "True")
        self.assertEqual(rows[2]["Active During Contest"], "True")
        self.assertEqual(rows[2]["Total Daily Walks During Contest"], "0")
        self.assertEqual(rows[2]["Total Steps During Contest"], "")
        self.assertEqual(rows[2]["Total Recorded Walks During Contest"], "2")
        self.assertEqual(
            rows[2]["Total Recorded Steps During Contest"], "6000"
        )

        self.assertEqual(rows[3]["Participant Name"], "User 5")
        self.assertEqual(rows[3]["Is New Signup"], "True")
        self.assertEqual(rows[3]["Active During Contest"], "False")
        self.assertEqual(rows[3]["Total Daily Walks During Contest"], "0")
        self.assertEqual(rows[3]["Total Steps During Contest"], "")
        self.assertEqual(rows[3]["Total Recorded Walks During Contest"], "0")
        self.assertEqual(rows[3]["Total Recorded Steps During Contest"], "")
