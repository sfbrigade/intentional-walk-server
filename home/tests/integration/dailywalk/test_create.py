from django.test import Client, TestCase


class ApiTestCase(TestCase):
    def setUp(self):
        # Test client
        self.client = Client()
        # Create a user
        response = self.client.post(
            path="/api/appuser/create",
            data={
                "name": "Abhay Kashyap",
                "email": "abhay@blah.com",
                "zip": "72185",
                "age": 99,
                "account_id": "12345",
            },
            content_type="application/json",
        )

        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "success", msg=fail_message)
        self.assertEqual(response_data["message"], "App User registered successfully", msg=fail_message)

        # Details for Daily walk even creation
        self.url = "/api/dailywalk/create"
        # Request parameters
        self.request_params = {
            "account_id": "12345",
            "daily_walks": [
                {
                    "date": "2020-02-22",
                    "steps": 500,
                    "distance": 1.3
                }
            ]
        }
        self.bulk_request_params = {
            "account_id": "12345",
            "daily_walks": [
                {"date": "2020-02-21", "steps": 1500, "distance": 2.1},
                {"date": "2020-02-22", "steps": 500, "distance": 0.8},
                {"date": "2020-02-23", "steps": 1000, "distance": 1.4},
            ]
        }
        # Content type
        self.content_type = "application/json"

    # Test a successful creation of a daily walk
    def test_create_dailywalk(self):

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
        self.assertEqual(response_data["payload"]["daily_walks"][0]["date"], self.request_params["daily_walks"][0]["date"], msg=fail_message)
        self.assertEqual(response_data["payload"]["daily_walks"][0]["steps"], self.request_params["daily_walks"][0]["steps"], msg=fail_message)
        self.assertEqual(response_data["payload"]["daily_walks"][0]["distance"], self.request_params["daily_walks"][0]["distance"], msg=fail_message)

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
            f'User does not exist for account - {self.request_params["account_id"]}. Please register first!',
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
        self.assertEqual(response_data["payload"]["account_id"], self.bulk_request_params["account_id"], msg=fail_message)
        self.assertEqual(len(response_data["payload"]["daily_walks"]), len(self.bulk_request_params["daily_walks"]))
        for i, daily_walk_data in enumerate(response_data["payload"]["daily_walks"]):
            self.assertEqual(daily_walk_data["date"], self.bulk_request_params["daily_walks"][i]["date"], msg=fail_message)
            self.assertEqual(daily_walk_data["steps"], self.bulk_request_params["daily_walks"][i]["steps"], msg=fail_message)
            self.assertEqual(daily_walk_data["distance"], self.bulk_request_params["daily_walks"][i]["distance"], msg=fail_message)
