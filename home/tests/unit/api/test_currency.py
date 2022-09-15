import json
from datetime import datetime

from dateutil.relativedelta import relativedelta
from django.test import Client, TestCase
from django.utils import timezone
from home.models.contest import Contest
from home.utils.generators import (
    AccountGenerator,
    DeviceGenerator,
    IntentionalWalkGenerator,
)
from home.views.api.currency import STEPS_PER_BADGE, STEPS_PER_COIN


class TestCurrency(TestCase):
    def setUp(self):
        self.account = next(
            AccountGenerator().generate(
                1,
                email="plum@clue.net",
                name="Professor Plum",
            )
        )

        self.device = next(DeviceGenerator([self.account]).generate(1))

        self.now = datetime.now().astimezone(timezone.get_default_timezone())
        start_promo = self.now - relativedelta(days=15 + 7)
        start = start_promo + relativedelta(days=7)
        end = self.now + relativedelta(days=15)

        self.contest = Contest.objects.create(
            start_promo=start_promo.date(),
            start=start.date(),
            end=end.date(),
        )

        self.client = Client()

    def generate_steps(self, steps: int):
        start = self.now
        end = self.now + relativedelta(hours=1)

        generator = IntentionalWalkGenerator([self.device])
        next(generator.generate(1, steps=steps, start=start, end=end))

    def post_request(self):
        response = self.client.post(
            "/api/currency/get",
            json.dumps({"account_id": str(self.device.device_id)}),
            content_type="application/json",
        )
        return response.json()

    def test_currency_no_contest(self):
        # Delete the Contest record we created
        self.contest.delete()

        # Make a POST request, expect the no active contest error
        response = self.client.post(
            "/api/currency/get",
            json.dumps({"account_id": str(self.device.device_id)}),
            content_type="application/json",
        )
        data = response.json()
        self.assertEqual(data.get("status"), "error")
        self.assertEqual(data.get("message"), "There is no active contest")

    def test_currency_missing_account_id(self):
        # Make a JSON POST request without any "account_id" key
        response = self.client.post(
            "/api/currency/get",
            json.dumps({}),
            content_type="application/json",
        )

        # Expect the account_id missing error
        data = response.json()
        self.assertEqual(data.get("status"), "error")
        self.assertEqual(
            data.get("message"),
            "Required input 'account_id' missing in the request",
        )

    def test_currency_coin(self):
        """Test that STEPS_PER_COIN translates into a single coin"""
        self.generate_steps(STEPS_PER_COIN)

        data = self.post_request()
        payload = data.get("payload")
        self.assertEqual(payload.get("steps"), STEPS_PER_COIN)
        self.assertEqual(payload.get("coins"), 1)
        self.assertEqual(payload.get("badges"), 0)

    def test_currency_badge(self):
        """Test that STEPS_PER_BADGE translates into a single badge
        with no coins"""
        self.generate_steps(STEPS_PER_BADGE)

        data = self.post_request()
        payload = data.get("payload")
        self.assertEqual(payload.get("steps"), STEPS_PER_BADGE)
        self.assertEqual(payload.get("coins"), 0)
        self.assertEqual(payload.get("badges"), 1)

    def test_currency(self):
        """Test that enough step build up a badge and two coins"""
        steps = STEPS_PER_BADGE + (STEPS_PER_COIN * 2)
        self.generate_steps(steps)

        data = self.post_request()
        payload = data.get("payload")
        self.assertEqual(payload.get("steps"), steps)
        self.assertEqual(payload.get("coins"), 2)
        self.assertEqual(payload.get("badges"), 1)

    def test_currency_none(self):
        """Test that without enough steps, we have no coins or badges"""
        steps = 5
        self.generate_steps(steps)

        data = self.post_request()
        payload = data.get("payload")
        self.assertEqual(payload.get("steps"), steps)
        self.assertEqual(payload.get("coins"), 0)
        self.assertEqual(payload.get("badges"), 0)
