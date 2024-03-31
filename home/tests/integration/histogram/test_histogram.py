from random import seed
from django.test import Client, TestCase

from home.tests.integration.views.api.utils import Login, generate_test_data


class ApiTestCase(TestCase):
    def setUp(self):
        seed(123)

        contest_id = generate_test_data()
        self.contest_id = contest_id
        self.client = Client()
        self.client.login(
            username=Login.username,
            password=Login.password,
        )
        self.content_type = "application/json"

    def tearDown(self) -> None:
        seed()
        return super().tearDown()

    def test_happy_paths(self):
        test_cases = [
            {
                "path": "/api/admin/users/histogram",
                "data": {
                    "field": "age",
                    "bin_size": 10,
                    "contest_id": self.contest_id,
                },
                "expect": {
                    "data": [
                        {
                            "bin_idx": 0,
                            "bin_start": 0,
                            "bin_end": 10,
                            "count": 0,
                        },
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
                            "bin_idx": 3,
                            "bin_start": 30,
                            "bin_end": 40,
                            "count": 0,
                        },
                        {
                            "bin_idx": 4,
                            "bin_start": 40,
                            "bin_end": 50,
                            "count": 0,
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
                    "unit": "years",
                    "bin_size": 10,
                },
            },
            {
                "path": "/api/admin/users/histogram",
                "data": {
                    "field": "age",
                    "bin_custom": "0,10,20,30,40,50,60,70,80",
                    "contest_id": self.contest_id,
                },
                "expect": {
                    "data": [
                        {
                            "bin_idx": 0,
                            "bin_start": 0,
                            "bin_end": 10,
                            "count": 0,
                        },
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
                            "bin_idx": 3,
                            "bin_start": 30,
                            "bin_end": 40,
                            "count": 0,
                        },
                        {
                            "bin_idx": 4,
                            "bin_start": 40,
                            "bin_end": 50,
                            "count": 0,
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
                        {
                            "bin_idx": 7,
                            "bin_start": 70,
                            "bin_end": 80,
                            "count": 0,
                        },
                        {
                            "bin_idx": 8,
                            "bin_start": 80,
                            "count": 0,
                        },
                    ],
                    "unit": "years",
                    "bin_custom": [0, 10, 20, 30, 40, 50, 60, 70, 80],
                },
            },
        ]
        for test_case in test_cases:
            with self.subTest(msg=test_case["path"]):
                response = self.client.get(
                    path=test_case["path"],
                    data=test_case["data"],
                    content_type=self.content_type,
                )
                self.assertEqual(
                    response.status_code,
                    200,
                    f"Received non-200 response: {response.json()}",
                )
                print(response.json())
                self.assertEqual(response.json(), test_case["expect"])

    def test_unsupported_paths(self):
        response = self.client.get(
            path="/api/admin/NOTSUPPORTEDMODELXD/histogram",
            data={},
            content_type=self.content_type,
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.get(
            path="/api/admin/users/histogram",
            data={
                "AIN'T GOT NO FIELDS": "NOPE",
            },
            content_type=self.content_type,
        )
        self.assertEqual(response.status_code, 422)
