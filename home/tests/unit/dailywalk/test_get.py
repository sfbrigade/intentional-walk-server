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

        # Create three daily walks
        self.daily_walks = [
            {"account_id": "12345", "event_id": "777", "date": "2020-02-21", "steps": 1500},
            {"account_id": "12345", "event_id": "888", "date": "2020-02-22", "steps": 500},
            {"account_id": "12345", "event_id": "999", "date": "2020-02-23", "steps": 1000},
        ]
        # Create daily walks
        for daily_walk in self.daily_walks:
            response = self.client.post(path="/api/dailywalk/create", data=daily_walk, content_type="application/json",)
            # Check for a successful response by the server
            self.assertEqual(response.status_code, 200)
            # Parse the response
            response_data = response.json()
            fail_message = f"Server response - {response_data}"
            self.assertEqual(response_data["status"], "success", msg=fail_message)
            self.assertEqual(response_data["message"], "Dailywalk recorded successfully", msg=fail_message)

        # Details for Daily walk list view
        self.url = "/api/dailywalk/get"
        # Request parameters
        self.request_params = {"account_id": "12345"}
        # Content type
        self.content_type = "application/json"

    def test_dailwalk_get_failure(self):
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

    def test_dailwalk_get(self):
        response = self.client.post(path=self.url, data=self.request_params, content_type=self.content_type)
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "success", msg=fail_message)
        self.assertIn("daily_walks", response_data, msg=fail_message)
        self.assertIn("total_steps", response_data, msg=fail_message)
        # Check if total steps is correct
        self.assertEqual(response_data["total_steps"], sum([dw["steps"] for dw in self.daily_walks]), msg=fail_message)
        # Check if the number of events match
        self.assertEqual(len(response_data["daily_walks"]), len(self.daily_walks), msg=fail_message)
        for walk in response_data["daily_walks"]:
            self.assertIn("date", walk, msg=fail_message)
            self.assertIn("steps", walk, msg=fail_message)
        # Check if they have the same exact data
        # Note that the response will always be ordered by the latest date
        self.assertEqual(
            response_data["daily_walks"],
            sorted(
                [{"date": dw["date"], "steps": dw["steps"]} for dw in self.daily_walks],
                key=lambda x: x["date"],
                reverse=True,
            ),
            msg=fail_message,
        )

    def test_dailwalk_get_withparam_reverse(self):
        self.request_params["reverse_order"] = True
        response = self.client.post(path=self.url, data=self.request_params, content_type=self.content_type)
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "success", msg=fail_message)
        self.assertIn("daily_walks", response_data, msg=fail_message)
        self.assertIn("total_steps", response_data, msg=fail_message)
        # Check if total steps is correct
        self.assertEqual(response_data["total_steps"], sum([dw["steps"] for dw in self.daily_walks]), msg=fail_message)
        # Check if the number of events match
        self.assertEqual(len(response_data["daily_walks"]), len(self.daily_walks), msg=fail_message)
        for walk in response_data["daily_walks"]:
            self.assertIn("date", walk, msg=fail_message)
            self.assertIn("steps", walk, msg=fail_message)
        # Check if they have the same exact data
        # Note that the response will now be ordered by the first date
        # So reverse=True for sort is removed
        self.assertEqual(
            sorted(response_data["daily_walks"], key=lambda x: x["date"]),
            sorted([{"date": dw["date"], "steps": dw["steps"]} for dw in self.daily_walks], key=lambda x: x["date"]),
            msg=fail_message,
        )

    def test_dailwalk_get_withparam_numwalks(self):
        self.request_params["num_walks"] = 2
        # Modify self.dailywalks to only include the latest two entires
        self.daily_walks = sorted(self.daily_walks, key=lambda x: x["date"], reverse=True)
        self.daily_walks = self.daily_walks[: self.request_params["num_walks"]]

        response = self.client.post(path=self.url, data=self.request_params, content_type=self.content_type)
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "success", msg=fail_message)
        self.assertIn("daily_walks", response_data, msg=fail_message)
        self.assertIn("total_steps", response_data, msg=fail_message)
        # Check if total steps is correct
        self.assertEqual(response_data["total_steps"], sum([dw["steps"] for dw in self.daily_walks]), msg=fail_message)
        # Check if the number of events match
        self.assertEqual(len(response_data["daily_walks"]), len(self.daily_walks), msg=fail_message)
        for walk in response_data["daily_walks"]:
            self.assertIn("date", walk, msg=fail_message)
            self.assertIn("steps", walk, msg=fail_message)
        # Check if they have the same exact data
        self.assertEqual(
            response_data["daily_walks"],
            sorted(
                [{"date": dw["date"], "steps": dw["steps"]} for dw in self.daily_walks],
                key=lambda x: x["date"],
                reverse=True,
            ),
            msg=fail_message,
        )

    def test_dailwalk_get_withparam_numwalks_reverse(self):
        self.request_params["num_walks"] = 2
        self.request_params["reverse_order"] = True

        # Modify self.dailywalks to only include the latest two entires
        self.daily_walks = sorted(self.daily_walks, key=lambda x: x["date"])
        self.daily_walks = self.daily_walks[: self.request_params["num_walks"]]
        response = self.client.post(path=self.url, data=self.request_params, content_type=self.content_type)
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "success", msg=fail_message)
        self.assertIn("daily_walks", response_data, msg=fail_message)
        self.assertIn("total_steps", response_data, msg=fail_message)
        # Check if total steps is correct
        self.assertEqual(response_data["total_steps"], sum([dw["steps"] for dw in self.daily_walks]), msg=fail_message)
        # Check if the number of events match
        self.assertEqual(len(response_data["daily_walks"]), len(self.daily_walks), msg=fail_message)
        for walk in response_data["daily_walks"]:
            self.assertIn("date", walk, msg=fail_message)
            self.assertIn("steps", walk, msg=fail_message)
        # Check if they have the same exact data
        self.assertEqual(
            sorted(response_data["daily_walks"], key=lambda x: x["date"]),
            sorted([{"date": dw["date"], "steps": dw["steps"]} for dw in self.daily_walks], key=lambda x: x["date"]),
            msg=fail_message,
        )
