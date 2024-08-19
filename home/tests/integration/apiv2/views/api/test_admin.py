import logging
from random import seed

from django.test import Client, TestCase

from .utils import Login, generate_test_data

logger = logging.getLogger(__name__)


class TestAdminViews(TestCase):
    contest0_id = None

    def setUp(self):
        seed(1)

    def tearDown(self) -> None:
        seed()
        return super().tearDown()

    @classmethod
    def setUpTestData(cls):
        cls.contest0_id = generate_test_data()

    def test_get_me(self):
        c = Client()
        # when unauthenticated, returns an empty response
        response = c.get("/api/v2/admin/me")
        self.assertEqual(response.status_code, 204)

        # log in
        self.assertTrue(Login.login(c))

        # when authenticated, returns the JSON representation of the user
        response = c.get("/api/v2/admin/me")
        data = response.json()
        self.assertEqual(data["username"], "testadmin")

    def test_get_home(self):
        c = Client()
        # when unauthenticated, returns an empty response
        response = c.get("/api/v2/admin/home")
        self.assertEqual(response.status_code, 401)

        # log in
        self.assertTrue(Login.login(c))
        response = c.get("/api/v2/admin/home")
        data = response.json()
        self.assertEqual(
            data,
            {
                "accounts_count": 5,  # 6 accounts - 1 tester
                "accounts_steps": 350000,  # 14 days * (10,000 + 15,000 steps/day)
                "accounts_distance": 280000,  # 14 days * (8,000 + 12,000 meters/day)
            },
        )

    def test_get_home_users_daily(self):
        c = Client()
        self.assertTrue(Login.login(c))
        response = c.get(
            f"/api/v2/admin/home/users/daily?contest_id={self.contest0_id}"
        )
        data = response.json()
        self.assertEqual(
            data,
            [
                ["Date", "Count"],
                ["3000-02-28T00:00:00", 0],
                ["3000-03-02T00:00:00", 3],
                ["3000-03-14T00:00:00", 0],
            ],
        )

    def test_get_home_users_cumulative(self):
        c = Client()
        self.assertTrue(Login.login(c))
        response = c.get(
            f"/api/v2/admin/home/users/cumulative?contest_id={self.contest0_id}"
        )
        data = response.json()
        self.assertEqual(
            data,
            [
                ["Date", "Count"],
                ["3000-02-28T00:00:00", 0],
                ["3000-03-02T00:00:00", 3],
                ["3000-03-14T00:00:00", 3],
            ],
        )

    def test_get_home_steps_daily(self):
        c = Client()
        self.assertTrue(Login.login(c))
        response = c.get(
            f"/api/v2/admin/home/steps/daily?contest_id={self.contest0_id}"
        )
        data = response.json()
        self.assertEqual(
            data,
            [
                ["Date", "Count"],
                ["3000-02-28T00:00:00", 25000],
                ["3000-03-01T00:00:00", 25000],
                ["3000-03-02T00:00:00", 25000],
                ["3000-03-03T00:00:00", 25000],
                ["3000-03-04T00:00:00", 25000],
                ["3000-03-05T00:00:00", 25000],
                ["3000-03-06T00:00:00", 25000],
                ["3000-03-07T00:00:00", 25000],
                ["3000-03-08T00:00:00", 25000],
                ["3000-03-09T00:00:00", 25000],
                ["3000-03-10T00:00:00", 25000],
                ["3000-03-11T00:00:00", 25000],
                ["3000-03-12T00:00:00", 25000],
                ["3000-03-13T00:00:00", 25000],
                ["3000-03-14T00:00:00", 0],
            ],
        )

    def test_get_home_steps_daily_invalid_contest_id(self):
        c = Client()
        self.assertTrue(Login.login(c))
        response = c.get(f"/api/v2/admin/home/steps/daily?contest_id=invalid")
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 404)
        # Parse the response
        response_data = response.content
        fail_message = f"Server response - {response_data}"
        self.assertIn(
            b"Cannot find contest with contest_id invalid",
            response_data,
            msg=fail_message,
        )

    def test_get_home_steps_cumulative(self):
        c = Client()
        self.assertTrue(Login.login(c))
        response = c.get(
            f"/api/v2/admin/home/steps/cumulative?contest_id={self.contest0_id}"
        )
        data = response.json()
        self.assertEqual(
            data,
            [
                ["Date", "Count"],
                ["3000-02-28T00:00:00", 25000],
                ["3000-03-01T00:00:00", 50000],
                ["3000-03-02T00:00:00", 75000],
                ["3000-03-03T00:00:00", 100000],
                ["3000-03-04T00:00:00", 125000],
                ["3000-03-05T00:00:00", 150000],
                ["3000-03-06T00:00:00", 175000],
                ["3000-03-07T00:00:00", 200000],
                ["3000-03-08T00:00:00", 225000],
                ["3000-03-09T00:00:00", 250000],
                ["3000-03-10T00:00:00", 275000],
                ["3000-03-11T00:00:00", 300000],
                ["3000-03-12T00:00:00", 325000],
                ["3000-03-13T00:00:00", 350000],
                ["3000-03-14T00:00:00", 350000],
            ],
        )

    def test_get_home_distance_daily(self):
        c = Client()
        self.assertTrue(Login.login(c))
        response = c.get(
            f"/api/v2/admin/home/distance/daily?contest_id={self.contest0_id}"
        )
        data = response.json()
        self.assertEqual(
            data,
            [
                ["Date", "Count"],
                ["3000-02-28T00:00:00", 20000],
                ["3000-03-01T00:00:00", 20000],
                ["3000-03-02T00:00:00", 20000],
                ["3000-03-03T00:00:00", 20000],
                ["3000-03-04T00:00:00", 20000],
                ["3000-03-05T00:00:00", 20000],
                ["3000-03-06T00:00:00", 20000],
                ["3000-03-07T00:00:00", 20000],
                ["3000-03-08T00:00:00", 20000],
                ["3000-03-09T00:00:00", 20000],
                ["3000-03-10T00:00:00", 20000],
                ["3000-03-11T00:00:00", 20000],
                ["3000-03-12T00:00:00", 20000],
                ["3000-03-13T00:00:00", 20000],
                ["3000-03-14T00:00:00", 0],
            ],
        )

    def test_get_home_distance_cumulative(self):
        c = Client()
        self.assertTrue(Login.login(c))
        response = c.get(
            f"/api/v2/admin/home/distance/cumulative?contest_id={self.contest0_id}"
        )
        data = response.json()
        self.assertEqual(
            data,
            [
                ["Date", "Count"],
                ["3000-02-28T00:00:00", 20000],
                ["3000-03-01T00:00:00", 40000],
                ["3000-03-02T00:00:00", 60000],
                ["3000-03-03T00:00:00", 80000],
                ["3000-03-04T00:00:00", 100000],
                ["3000-03-05T00:00:00", 120000],
                ["3000-03-06T00:00:00", 140000],
                ["3000-03-07T00:00:00", 160000],
                ["3000-03-08T00:00:00", 180000],
                ["3000-03-09T00:00:00", 200000],
                ["3000-03-10T00:00:00", 220000],
                ["3000-03-11T00:00:00", 240000],
                ["3000-03-12T00:00:00", 260000],
                ["3000-03-13T00:00:00", 280000],
                ["3000-03-14T00:00:00", 280000],
            ],
        )

    def test_get_contests(self):
        c = Client()
        self.assertTrue(Login.login(c))
        response = c.get("/api/v2/admin/contests")
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["contest_id"], self.contest0_id)

    def test_get_users(self):
        c = Client()
        self.assertTrue(Login.login(c))

        response = c.get("/api/v2/admin/users")
        data = (response.json())["users"]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 5)  # 6 accounts - 1 tester

        response = c.get(
            f"/api/v2/admin/users?contest_id={self.contest0_id}&is_tester=invalid"
        )
        self.assertEqual(response.status_code, 422)

        response = c.get(f"/api/v2/admin/users?contest_id={self.contest0_id}")
        self.assertEqual(response.status_code, 200)
        data = (response.json())["users"]
        self.assertEqual(len(data), 4)  # 5 accounts in the contest - 1 tester
        # default ordering is by name
        self.assertEqual(data[0]["name"], "User 2")
        self.assertEqual(data[0]["is_new"], False)
        self.assertEqual(data[0]["dw_count"], 7)
        self.assertEqual(data[0]["dw_steps"], 70000)
        self.assertEqual(data[0]["dw_distance"], 56000)
        self.assertEqual(data[1]["name"], "User 3")
        self.assertEqual(data[1]["is_new"], True)
        self.assertEqual(data[1]["dw_count"], 7)
        self.assertEqual(data[1]["dw_steps"], 105000)
        self.assertEqual(data[1]["dw_distance"], 84000)
        self.assertEqual(data[2]["name"], "User 4")
        self.assertEqual(data[2]["is_new"], True)
        self.assertEqual(data[2]["dw_count"], 0)
        self.assertEqual(data[2]["dw_steps"], 0)
        self.assertEqual(data[2]["dw_distance"], 0)
        self.assertEqual(data[3]["name"], "User 5")
        self.assertEqual(data[3]["is_new"], True)
        self.assertEqual(data[3]["dw_count"], 0)
        self.assertEqual(data[3]["dw_steps"], 0)
        self.assertEqual(data[3]["dw_distance"], 0)

        response = c.get(
            f"/api/v2/admin/users?contest_id={self.contest0_id}&is_tester=true"
        )
        self.assertEqual(response.status_code, 200)
        data = (response.json())["users"]
        self.assertEqual(len(data), 1)  # 1 tester
        # query
        response = c.get("/api/v2/admin/users?query=User 2")
        self.assertEqual(response.status_code, 200)
        data = (response.json())["users"]

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "User 2")

        response = c.get("/api/v2/admin/users?query=aintgonfindmeatall")
        self.assertEqual(response.status_code, 200)
        data = (response.json())["users"]
        self.assertEqual(len(data), 0)

        # sort
        response = c.get("/api/v2/admin/users?order_by=age")
        data = (response.json())["users"]
        self.assertEqual(response.status_code, 200)
        ages = [user["age"] for user in data]
        ascending_order = all(a <= b for a, b in zip(ages, ages[1:]))
        self.assertTrue(ascending_order)

        response = c.get("/api/v2/admin/users?order_by=-age")
        data = (response.json())["users"]
        self.assertEqual(ages, [user["age"] for user in data[::-1]])

    def test_get_users_by_zip(self):
        c = Client()
        # when unauthenticated, returns status code 401
        response = c.get("/api/v2/admin/users/zip")
        self.assertEqual(response.status_code, 401)

        # authenticated
        self.assertTrue(Login.login(c))

        response = c.get(f"/api/v2/admin/users/zip")
        data = response.json()
        self.assertEqual(
            data,
            {
                "total": {"94102": 1, "94103": 2, "94104": 2},
            },
        )

        response = c.get(
            f"/api/v2/admin/users/zip?contest_id={self.contest0_id}"
        )
        data = response.json()
        self.assertEqual(
            data,
            {
                "total": {"94103": 2, "94104": 2},
                "new": {"94103": 1, "94104": 2},
            },
        )

    def test_get_users_active_by_zip(self):
        c = Client()
        # when unauthenticated, returns status code 401
        response = c.get(
            f"/api/v2/admin/users/zip/active?contest_id={self.contest0_id}"
        )
        self.assertEqual(response.status_code, 401)

        # authenticated
        self.assertTrue(Login.login(c))

        # no  contest_id given
        response = c.get(f"/api/v2/admin/users/zip/active")
        self.assertEqual(response.status_code, 404)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(
            response_data["detail"],
            "Cannot find contest_id None",
            msg=fail_message,
        )

        response = c.get(
            f"/api/v2/admin/users/zip/active?contest_id={self.contest0_id}"
        )
        data = response.json()
        self.assertEqual(
            data,
            {
                "total": {"94103": 2, "94104": 1},
                "new": {"94103": 1, "94104": 1},
            },
        )

    def test_get_users_median_steps_by_zip(self):
        c = Client()
        # when unauthenticated, returns status code 401
        response = c.get(
            f"/api/v2/admin/users/zip/steps?contest_id={self.contest0_id}"
        )
        self.assertEqual(response.status_code, 401)

        # authenticated
        self.assertTrue(Login.login(c))

        # no  contest_id given
        response = c.get(f"/api/v2/admin/users/zip/steps")
        self.assertEqual(response.status_code, 404)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(
            response_data["detail"],
            "Cannot find contest_id None",
            msg=fail_message,
        )

        response = c.get(
            f"/api/v2/admin/users/zip/steps?contest_id={self.contest0_id}"
        )
        data = response.json()
        self.assertEqual(
            data,
            {
                "all": 87500.0,
                "94103": 87500.0,
            },  # median of [70k, 105k] = avg of the two = 87.5k
        )
