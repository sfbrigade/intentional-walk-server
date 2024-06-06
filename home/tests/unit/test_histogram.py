from random import seed
from datetime import date, timedelta, timezone, datetime
from django.test import TestCase
from home.models import Account, Contest, Device
from home.models.dailywalk import DailyWalk
from home.models.intentionalwalk import IntentionalWalk
from home.models.leaderboard import Leaderboard
from home.tests.integration.views.api.utils import generate_test_data
from home.views.api.histogram.serializers import HistogramReqSerializer


class TestHistogram(TestCase):
    def setUp(self):
        seed(123)
        self.contest_id = generate_test_data()
        no_participants = Contest(
            start=datetime(5000, 1, 2, tzinfo=timezone.utc),
            end=datetime(5000, 1, 31, tzinfo=timezone.utc),
            start_promo=datetime(5000, 1, 1, tzinfo=timezone.utc),
            start_baseline=datetime(5000, 1, 1, tzinfo=timezone.utc),
        )
        no_participants.save()
        self.empty_contest_id = str(no_participants.contest_id)

    def tearDown(self) -> None:
        seed()
        return super().tearDown()

    def create_test_cases(self):
        return [
            {
                "name": "invalid model",
                "input": {
                    "field": "steps",
                    "bin_size": 10,
                    "model": Contest,
                },
                "expect": {
                    "error": "not supported",
                },
            },
            {
                "name": "empty contest with no user",
                "input": {
                    "field": "age",
                    "bin_size": 10,
                    "model": Account,
                    "contest_id": self.empty_contest_id,
                },
                "expect": {
                    "response": {
                        "data": [],
                    }
                },
            },
            {
                "name": "require contest id data for Leaderboard",
                "input": {
                    "field": "steps",
                    "bin_size": 10,
                    "model": Leaderboard,
                },
                "expect": {
                    "error": "contest_id is required",
                },
            },
            {
                "name": "contest and date are mutually exclusive for Leaderboard",
                "input": {
                    "field": "steps",
                    "start_date": date(2021, 1, 1),
                    "bin_size": 10,
                    "contest_id": self.contest_id,
                    "model": Leaderboard,
                },
                "expect": {
                    "error": "mutually exclusive",
                },
            },
            {
                "name": "invalid contest id",
                "input": {
                    "field": "steps",
                    "bin_size": 10,
                    "model": Leaderboard,
                    "contest_id": 999,
                },
                "expect": {
                    "error": "does not exist",
                },
            },
            {
                "name": "required url parameter 'field'",
                "input": {
                    "bin_size": 10,
                    "model": Leaderboard,
                },
                "expect": {
                    "error": "field is required",
                },
            },
            {
                "name": "bin parameters are mutually exclusive",
                "input": {
                    "field": "steps",
                    "bin_size": 10,
                    "bin_count": 5,
                    "bin_custom": "1,2,3,4,5",
                    "model": Leaderboard,
                },
                "expect": {
                    "error": "are mutually exclusive",
                },
            },
            {
                "name": "one of bin_size, bin_count, or bin_custom is required",
                "input": {
                    "field": "steps",
                    "model": Leaderboard,
                },
                "expect": {
                    "error": "bin_size, bin_count, or bin_custom",
                },
            },
            {
                "name": "invalid bin size",
                "input": {
                    "field": "steps",
                    "bin_size": -3,
                    "model": Leaderboard,
                },
                "expect": {
                    "error": "greater than",
                },
            },
            {
                "name": "invalid bin count",
                "input": {
                    "field": "steps",
                    "bin_count": -1,
                    "model": Leaderboard,
                },
                "expect": {
                    "error": "greater than",
                },
            },
            {
                "name": "invalid parameter for `field`",
                "input": {
                    "field": "unsupported_field",
                    "bin_size": 10,
                    "model": Leaderboard,
                },
                "expect": {
                    "error": "unsupported_field is not supported",
                },
            },
            {
                "name": "unsupported `field` for Account",
                "input": {
                    "field": "steps",
                    "bin_size": 10,
                    "model": Account,
                },
                "expect": {
                    "error": "steps is not supported",
                },
            },
            {
                "name": "unsupported `Model`",
                "input": {
                    "field": "steps",
                    "bin_size": 10,
                    "model": Contest,
                },
                "expect": {
                    "error": "not supported",
                },
            },
            {
                "name": "missing `Model`",
                "input": {
                    "field": "steps",
                    "bin_count": 10,
                },
                "expect": {
                    "error": "Model is required",
                },
            },
            {
                "name": "contest with no participants for Leaderboard",
                "input": {
                    "field": "steps",
                    "bin_size": 10,
                    "contest_id": self.contest_id,
                    "model": Leaderboard,
                },
                "expect": {
                    "response": {
                        "data": [],
                        "unit": "steps",
                        "bin_size": 10,
                    }
                },
            },
            {
                "name": "happy: contest with participants for DailyWalk",
                "input": {
                    "field": "steps",
                    "bin_count": 5,
                    "contest_id": self.contest_id,
                    "model": DailyWalk,
                },
                "expect": {
                    "response": {
                        "data": [
                            {
                                "bin_idx": 1,
                                "bin_start": 3750,
                                "bin_end": 7500,
                                "count": 14,
                            },
                            {
                                "bin_idx": 2,
                                "bin_start": 7500,
                                "bin_end": 11250,
                                "count": 14,
                            },
                            {
                                "bin_idx": 4,
                                "bin_start": 15000,
                                "bin_end": 18750,
                                "count": 14,
                            },
                        ],
                        "bin_count": 5,
                        "bin_size": 3750,
                    }
                },
            },
            {
                "name": "happy: valid Account request by `date`",
                "input": {
                    "field": "age",
                    "bin_size": 10,
                    "model": Account,
                    "date_start": date(2021, 1, 1),
                    "date_end": date(2021, 1, 31),
                },
                "expect": {
                    "response": {
                        "data": [
                            {
                                "bin_idx": 1,
                                "bin_start": 10,
                                "bin_end": 20,
                                "count": 1,
                            },
                            {
                                "bin_idx": 2,
                                "bin_start": 20,
                                "bin_end": 30,
                                "count": 1,
                            },
                            {
                                "bin_idx": 5,
                                "bin_start": 50,
                                "bin_end": 60,
                                "count": 2,
                            },
                            {
                                "bin_idx": 6,
                                "bin_start": 60,
                                "bin_end": 70,
                                "count": 2,
                            },
                        ],
                        "bin_count": 5,
                        "bin_size": 3750,
                    }
                },
            },
            {
                "name": "happy: valid Account request by `contest`",
                "input": {
                    "field": "age",
                    "bin_size": 10,
                    "model": Account,
                    "contest_id": self.contest_id,
                },
                "expect": {
                    "response": {
                        "data": [
                            {
                                "bin_idx": 2,
                                "bin_start": 20,
                                "bin_end": 30,
                                "count": 1,
                            },
                            {
                                "bin_idx": 5,
                                "bin_start": 50,
                                "bin_end": 60,
                                "count": 2,
                            },
                            {
                                "bin_idx": 6,
                                "bin_start": 60,
                                "bin_end": 70,
                                "count": 1,
                            },
                        ],
                        "bin_count": 5,
                        "bin_size": 3750,
                    }
                },
            },
            {
                "name": "happy: valid IntentionalWalk by contest",
                "input": {
                    "field": "steps",
                    "bin_size": 10,
                    "model": IntentionalWalk,
                    "contest_id": self.contest_id,
                },
                "expect": {
                    "response": {
                        "data": [
                            {
                                "bin_idx": 100,
                                "bin_start": 1000,
                                "bin_end": 1010,
                                "count": 5,
                            },
                            {
                                "bin_idx": 200,
                                "bin_start": 2000,
                                "bin_end": 2010,
                                "count": 5,
                            },
                            {
                                "bin_idx": 300,
                                "bin_start": 3000,
                                "bin_end": 3010,
                                "count": 5,
                            },
                        ],
                        "bin_count": 5,
                        "bin_size": 3750,
                    }
                },
            },
            {
                "name": "happy: valid Account request by `contest`, using custom bins",
                "input": {
                    "field": "age",
                    "bin_custom": "5,18,24,33,55",
                    "model": Account,
                    "contest_id": self.contest_id,
                },
                "expect": {
                    "response": {
                        "data": [
                            {
                                "bin_start": 18,
                                "bin_end": 24,
                                "bin_idx": 1,
                                "count": 1,
                            },
                            {
                                "bin_start": 33,
                                "bin_end": 55,
                                "bin_idx": 3,
                                "count": 2,
                            },
                            {
                                "bin_start": 55,
                                "bin_end": 67,
                                "bin_idx": 4,
                                "count": 1,
                            },
                        ]
                    }
                },
            },
        ]

    def test_validate_histogram_request(self):
        for test_case in self.create_test_cases():
            test_case_name = test_case["name"]
            with self.subTest(msg=test_case_name):
                input_data = test_case["input"]
                expect = test_case["expect"]
                serializer = HistogramReqSerializer(
                    data=input_data, model=input_data.get("model", None)
                )
                is_valid = serializer.is_valid()
                errors = "".join(
                    f"{k}:{v}" for k, v in serializer.errors.items()
                )
                if expect.get("error"):
                    self.assertEqual(is_valid, False)
                    self.assertTrue(
                        len(serializer.errors) > 0,
                        msg="Missing errors",
                    )
                    self.assertIn(
                        expect["error"],
                        errors,
                    )
                else:
                    self.assertTrue(
                        is_valid,
                        msg=f"Unexpected errors: {errors}",
                    )
                    self.assertEqual(serializer.errors, {})
                    got = list(serializer.validated_data["query_set"])
                    want = expect["response"]["data"]
                    self.maxDiff = None
                    self.assertEqual(
                        got,
                        want,
                        msg=f"{test_case_name}: Received: {got}. Expected {want}",
                    )
