from django.test import Client, TestCase

from home.models import Account


class ApiTestCase(TestCase):
    def setUp(self):
        # Test client
        self.client = Client()

        # Device ID is passed to the API as "account_id",
        self.device_id = "12345"
        self.email = "abhay@blah.com"
        self.request_params = {
            "name": "Abhay Kashyap",
            "email": self.email,
            "zip": "94132",
            "age": 99,
            "account_id": self.device_id,
        }
        # Create a user
        response = self.client.post(
            path="/api/v2/appuser",
            data=self.request_params,
            content_type="application/json",
        )

        # Check for a successful response by the server
        self.assertEqual(response.status_code, 201)

        # Create three daily walks
        self.daily_walks = {
            "account_id": "12345",
            "daily_walks": [
                {"date": "2020-02-21", "steps": 1500, "distance": 2.1},
                {"date": "2020-02-22", "steps": 500, "distance": 0.8},
                {"date": "2020-02-23", "steps": 1000, "distance": 1.4},
            ],
        }
        # Create daily walks
        response = self.client.post(
            path="/api/v2/dailywalk",
            data=self.daily_walks,
            content_type="application/json",
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 201)

        # Details for Daily walk list view
        self.url = "/api/v2/dailywalk"
        # Request parameters
        self.request_params = {"account_id": "12345"}
        # Content type
        self.content_type = "application/json"

    def test_dailywalk_get_failure(self):
        self.request_params["account_id"] = "0000000"

        # Send the request
        response = self.client.get(
            path=f"{self.url}/{self.request_params['account_id']}"
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 404)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(
            response_data["detail"],
            "Unregistered device - "
            f'{self.request_params["account_id"]}.'
            " Please register first!",
            msg=fail_message,
        )

    def test_dailywalk_get_missing_account_id(self):
        request_params = self.request_params.copy()
        del request_params["account_id"]

        # Send the request
        response = self.client.get(path=f"{self.url}/")
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 404)
        # Parse the response
        response_data = response.content
        fail_message = f"Server response - {response_data}"
        self.assertIn(b"Not Found", response_data, msg=fail_message)

    def test_dailywalk_get(self):
        response = self.client.get(
            path=f"{self.url}/{self.request_params['account_id']}",
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertIn("daily_walks", response_data, msg=fail_message)
        self.assertIn("total_steps", response_data, msg=fail_message)
        self.assertIn("total_distance", response_data, msg=fail_message)
        for walk in response_data["daily_walks"]:
            self.assertIn("date", walk, msg=fail_message)
            self.assertIn("steps", walk, msg=fail_message)
            self.assertIn("distance", walk, msg=fail_message)
        # Check if total steps is correct
        self.assertEqual(
            response_data["total_steps"],
            sum([dw["steps"] for dw in self.daily_walks["daily_walks"]]),
            msg=fail_message,
        )
        # Check if total distance is correct
        self.assertEqual(
            response_data["total_distance"],
            sum([dw["distance"] for dw in self.daily_walks["daily_walks"]]),
            msg=fail_message,
        )
        # Check if the number of events match
        self.assertEqual(
            len(response_data["daily_walks"]),
            len(self.daily_walks["daily_walks"]),
            msg=fail_message,
        )
        # Check if they have the same exact data
        # Note that the response will always be ordered by the latest date
        self.assertEqual(
            response_data["daily_walks"],
            sorted(
                [
                    {
                        "date": dw["date"],
                        "steps": dw["steps"],
                        "distance": dw["distance"],
                    }
                    for dw in self.daily_walks["daily_walks"]
                ],
                key=lambda x: x["date"],
                reverse=True,
            ),
            msg=fail_message,
        )

    # Check if walks across multiple accounts tied to the same
    # email are aggregated
    def test_dailywalk_get_aggregated(self):

        # Create a second account from a different device but
        # with the same email
        response = self.client.post(
            path="/api/v2/appuser",
            data={
                "name": "Abhay Kashyap",
                "email": "abhay@blah.com",
                "zip": "94102",
                "age": 99,
                "account_id": "54321",
            },
            content_type="application/json",
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 201)

        # Create a third account from a different device but with the same email
        response = self.client.post(
            path="/api/v2/appuser",
            data={
                "name": "Abhay Kashyap",
                "email": "abhay@blah.com",
                "zip": "94102",
                "age": 99,
                "account_id": "99999",
            },
            content_type="application/json",
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 201)

        # Create additional walks
        new_daily_walks = {
            "account_id": "54321",
            "daily_walks": [
                {"date": "2020-02-12", "steps": 444, "distance": 0.4},
                {"date": "2020-02-13", "steps": 666, "distance": 0.6},
            ],
        }
        response = self.client.post(
            path="/api/v2/dailywalk",
            data=new_daily_walks,
            content_type="application/json",
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 201)

        # Update the daily walks for the tests to run
        # Note that to aggregate data, the updated event for "2020-02-12"
        # from account "99999" must be used instead of the update from "54321"
        # So pop that entry from new_daily_walks & update daily walks
        new_daily_walks["daily_walks"].pop(0)
        self.daily_walks["daily_walks"] += new_daily_walks["daily_walks"]

        # Create another entry for the same first date but from a different
        # account. This should create a new row but when aggregating data,
        # this entry should supercede the older entry for the same day from
        # the different account
        new_daily_walks = {
            "account_id": "99999",
            "daily_walks": [
                {"date": "2020-02-14", "steps": 999, "distance": 0.9},
                {"date": "2020-02-12", "steps": 555, "distance": 0.5},
            ],
        }
        response = self.client.post(
            path="/api/v2/dailywalk",
            data=new_daily_walks,
            content_type="application/json",
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 201)

        # Update the daily walks for the tests to run
        self.daily_walks["daily_walks"] += new_daily_walks["daily_walks"]

        response = self.client.get(
            path=f"{self.url}/{self.request_params['account_id']}",
            data=self.request_params,
            content_type=self.content_type,
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertIn("daily_walks", response_data, msg=fail_message)
        self.assertIn("total_steps", response_data, msg=fail_message)
        self.assertIn("total_distance", response_data, msg=fail_message)
        for walk in response_data["daily_walks"]:
            self.assertIn("date", walk, msg=fail_message)
            self.assertIn("steps", walk, msg=fail_message)
            self.assertIn("distance", walk, msg=fail_message)
        # Check if total steps is correct
        self.assertEqual(
            response_data["total_steps"],
            sum([dw["steps"] for dw in self.daily_walks["daily_walks"]]),
            msg=fail_message,
        )
        # Check if total steps is correct
        self.assertEqual(
            response_data["total_distance"],
            sum([dw["distance"] for dw in self.daily_walks["daily_walks"]]),
            msg=fail_message,
        )
        # Check if the number of events match
        self.assertEqual(
            len(response_data["daily_walks"]),
            len(self.daily_walks["daily_walks"]),
            msg=fail_message,
        )
        # Check if they have the same exact data
        # Note that the response will always be ordered by the latest date
        self.assertEqual(
            response_data["daily_walks"],
            sorted(
                [
                    {
                        "date": dw["date"],
                        "steps": dw["steps"],
                        "distance": dw["distance"],
                    }
                    for dw in self.daily_walks["daily_walks"]
                ],
                key=lambda x: x["date"],
                reverse=True,
            ),
            msg=fail_message,
        )

    # Test invalid method
    def test_dailywalk_get_invalid_methods(self):
        # Test not allowed get method
        response = self.client.get(
            path=self.url,
            data=self.request_params,
            content_type=self.content_type,
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 405)
        # Parse the response
        response_data = response.content
        fail_message = f"Server response - {response_data}"
        self.assertEqual(
            response_data, b"Method not allowed", msg=fail_message
        )

        # Test not allowed patch method
        response = self.client.patch(
            path=self.url,
            data=self.request_params,
            content_type=self.content_type,
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 405)
        # Parse the response
        response_data = response.content
        fail_message = f"Server response - {response_data}"
        self.assertEqual(
            response_data, b"Method not allowed", msg=fail_message
        )

        # Test not allowed put method
        response = self.client.put(
            path=self.url,
            data=self.request_params,
            content_type=self.content_type,
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 405)
        # Parse the response
        response_data = response.content
        fail_message = f"Server response - {response_data}"
        self.assertEqual(
            response_data, b"Method not allowed", msg=fail_message
        )

        # Test not allowed delete method
        response = self.client.delete(
            path=self.url,
            data=self.request_params,
            content_type=self.content_type,
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 405)
        # Parse the response
        response_data = response.content
        fail_message = f"Server response - {response_data}"
        self.assertEqual(
            response_data, b"Method not allowed", msg=fail_message
        )
