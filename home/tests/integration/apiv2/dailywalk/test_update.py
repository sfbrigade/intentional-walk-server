from django.test import Client, TestCase


class ApiTestCase(TestCase):
    def setUp(self):
        # Test client
        self.client = Client()
        # Create a user
        response = self.client.post(
            path="/api/v2/appuser",
            data={
                "name": "Abhay Kashyap",
                "email": "abhay@blah.com",
                "zip": "94102",
                "age": 99,
                "account_id": "12345",
            },
            content_type="application/json",
        )

        # Check for a successful response by the server
        self.assertEqual(response.status_code, 201)

        # Details for Daily walk even creation
        self.url = "/api/v2/dailywalk"
        # Request parameters
        self.request_params = {
            "account_id": "12345",
            "daily_walks": [
                {"date": "2020-02-22", "steps": 500, "distance": 1.3}
            ],
        }
        # Content type
        self.content_type = "application/json"

        # Create a daily walk
        # Send the request
        response = self.client.post(
            path=self.url,
            data=self.request_params,
            content_type=self.content_type,
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 201)

    # Test creation of a daily walk for the same date twice
    def test_update_steps_dailywalk_success(self):

        # Send the second request but ensure its an update
        self.request_params["daily_walks"][0]["steps"] = 1000
        self.request_params["daily_walks"][0]["distance"] = 2.1

        response = self.client.post(
            path=self.url,
            data=self.request_params,
            content_type=self.content_type,
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 201)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(
            response_data["daily_walks"][0]["date"],
            self.request_params["daily_walks"][0]["date"],
            msg=fail_message,
        )
        self.assertEqual(
            response_data["daily_walks"][0]["steps"],
            self.request_params["daily_walks"][0]["steps"],
            msg=fail_message,
        )
        self.assertEqual(
            response_data["daily_walks"][0]["distance"],
            self.request_params["daily_walks"][0]["distance"],
            msg=fail_message,
        )
