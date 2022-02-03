from django.test import Client, TestCase

from home.models import Contest, Device

class ApiTestCase(TestCase):
    def setUp(self):
        # Test client
        self.client = Client()

        # Device ID is passed to the API as "account_id",
        self.device_id = "12345"

        # Create a user
        response = self.client.post(
            path="/api/appuser/create",
            data={
                "name": "Abhay Kashyap",
                "email": "abhay@blah.com",
                "zip": "72185",
                "age": 99,
                "account_id": self.device_id,
            },
            content_type="application/json",
        )

        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "success", msg=fail_message)
        self.assertEqual(
            response_data["message"], "Device registered & account registered successfully", msg=fail_message
        )

        # Details for Daily walk even creation
        self.url = "/api/dailywalk/create"
        # Request parameters
        self.request_params = {
            "account_id": "12345",
            "daily_walks": [{"date": "3000-02-22", "steps": 500, "distance": 1.3}],
        }
        self.bulk_request_params = {
            "account_id": "12345",
            "daily_walks": [
                {"date": "3000-02-21", "steps": 1500, "distance": 2.1},
                {"date": "3000-02-22", "steps": 500, "distance": 0.8},
                {"date": "3000-02-23", "steps": 1000, "distance": 1.4},
            ],
        }
        # Content type
        self.content_type = "application/json"

    # Test a successful creation of a daily walk (within a contest)
    def test_create_dailywalk(self):
        # Create a contest
        contest = Contest()
        contest.start_baseline = "3000-01-01"
        contest.start_promo = "3000-02-01"
        contest.start = "3000-02-01"
        contest.end = "3000-02-28"
        contest.save()

        # Verify that the user has no contests
        acct = Device.objects.get(device_id=self.device_id).account
        self.assertFalse(acct.contests.exists())

        # Send the request
        response = self.client.post(path=self.url, data=self.request_params, content_type=self.content_type)
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "success", msg=fail_message)
        self.assertEqual(response_data["message"], "Dailywalks recorded successfully", msg=fail_message)
        self.assertEqual(response_data["payload"]["account_id"], self.request_params["account_id"], msg=fail_message)
        self.assertEqual(
            response_data["payload"]["daily_walks"][0]["date"],
            self.request_params["daily_walks"][0]["date"],
            msg=fail_message,
        )
        self.assertEqual(
            response_data["payload"]["daily_walks"][0]["steps"],
            self.request_params["daily_walks"][0]["steps"],
            msg=fail_message,
        )
        self.assertEqual(
            response_data["payload"]["daily_walks"][0]["distance"],
            self.request_params["daily_walks"][0]["distance"],
            msg=fail_message,
        )

        # Verify that the user now has a contest
        self.assertEqual(1, len(acct.contests.all()))


    # Test that a daily walk outside of a contest does not show up as
    # contest participation for that user
    def test_create_dailywalk_outside_contests(self):
        # Create a contest
        contest = Contest()
        contest.start_baseline = None
        contest.start_promo = "3000-03-01"
        contest.start = "3000-03-01"
        contest.end = "3000-03-31"
        contest.save()

        # Verify that the user has no contests
        acct = Device.objects.get(device_id=self.device_id).account
        self.assertFalse(acct.contests.exists())

        # Send the request
        response = self.client.post(path=self.url, data=self.request_params, content_type=self.content_type)
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)

        # Verify that the user still has no contests
        self.assertFalse(acct.contests.exists())


    # Test that daily walk data sent as baseline data shows up as baseline data
    def test_create_baseline_dailywalk(self):
        # Create a contest
        contest = Contest()
        contest.start_baseline = "3000-02-01"
        contest.start_promo = "3000-03-01"
        contest.start = "3000-03-01"
        contest.end = "3000-03-31"
        contest.save()

        # Verify that the user has no contests
        acct = Device.objects.get(device_id=self.device_id).account
        self.assertFalse(acct.contests.exists())

        # Verify that the user has no contests
        self.assertFalse(acct.contests.exists())

        # Send baseline data
        baseline_data = {
            "account_id": "12345",
            "daily_walks": [{"date": "3000-02-22", "steps": 500, "distance": 1.3}],
        }
        response = self.client.post(path=self.url, data=baseline_data, content_type=self.content_type)
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)

        # Verify that the user still has no contests
        self.assertFalse(acct.contests.exists())


    # Test creation of a daily walk with an invalid user account
    def test_create_dailywalk_invalidaccount(self):

        self.request_params["account_id"] = "0000000"

        # Send the request
        response = self.client.post(path=self.url, data=self.request_params, content_type=self.content_type)
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "error", msg=fail_message)
        self.assertEqual(
            response_data["message"],
            f'Unregistered device - {self.request_params["account_id"]}. Please register first!',
            msg=fail_message,
        )

    # Test creation of a daily walk with a missing field
    def test_create_dailywalk_missing_steps(self):

        del self.request_params["daily_walks"][0]["steps"]

        # Send the request
        response = self.client.post(path=self.url, data=self.request_params, content_type=self.content_type)
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "error", msg=fail_message)
        self.assertEqual(
            response_data["message"], "Required input 'steps' missing in the request", msg=fail_message,
        )

    # Test a successful creation of a daily walk
    def test_bulk_create_dailywalk(self):

        # Send the request
        response = self.client.post(path=self.url, data=self.bulk_request_params, content_type=self.content_type)
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "success", msg=fail_message)
        self.assertEqual(response_data["message"], "Dailywalks recorded successfully", msg=fail_message)
        self.assertEqual(
            response_data["payload"]["account_id"], self.bulk_request_params["account_id"], msg=fail_message
        )
        self.assertEqual(len(response_data["payload"]["daily_walks"]), len(self.bulk_request_params["daily_walks"]))
        for i, daily_walk_data in enumerate(response_data["payload"]["daily_walks"]):
            self.assertEqual(
                daily_walk_data["date"], self.bulk_request_params["daily_walks"][i]["date"], msg=fail_message
            )
            self.assertEqual(
                daily_walk_data["steps"], self.bulk_request_params["daily_walks"][i]["steps"], msg=fail_message
            )
            self.assertEqual(
                daily_walk_data["distance"], self.bulk_request_params["daily_walks"][i]["distance"], msg=fail_message
            )
