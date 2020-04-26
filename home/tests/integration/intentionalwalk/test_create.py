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
        self.url = "/api/intentionalwalk/create"
        # Request parameters
        self.request_params = {
            "account_id": "12345",
            "intentional_walks": [
                {
                    "event_id": "8888",
                    "start": "2020-02-21T12:15:00-05:00",
                    "end": "2020-02-21T12:45:00-05:00",
                    "steps": 500,
                    "distance": 1.3,
                    "pause_time": 456
                }
            ]
        }
        # Content type
        self.content_type = "application/json"

    # Test a successful creation of a intentional walk
    def test_create_intentionalwalk(self):

        # Send the request
        response = self.client.post(path=self.url, data=self.request_params, content_type=self.content_type)
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "success", msg=fail_message)
        self.assertEqual(response_data["message"], "Intentional Walks recorded successfully", msg=fail_message)
        self.assertEqual(response_data["payload"]["account_id"], self.request_params["account_id"], msg=fail_message)
        print(str(response_data))
        self.assertEqual(response_data["payload"]["intentional_walks"][0]["event_id"], self.request_params["intentional_walks"][0]["event_id"], msg=fail_message)
        self.assertEqual(response_data["payload"]["intentional_walks"][0]["start"], self.request_params["intentional_walks"][0]["start"], msg=fail_message)
        self.assertEqual(response_data["payload"]["intentional_walks"][0]["end"], self.request_params["intentional_walks"][0]["end"], msg=fail_message)
        self.assertEqual(response_data["payload"]["intentional_walks"][0]["steps"], self.request_params["intentional_walks"][0]["steps"], msg=fail_message)
        self.assertEqual(response_data["payload"]["intentional_walks"][0]["pause_time"], self.request_params["intentional_walks"][0]["pause_time"], msg=fail_message)
        self.assertEqual(response_data["payload"]["intentional_walks"][0]["distance"], self.request_params["intentional_walks"][0]["distance"], msg=fail_message)

    # Test creation of a intentional walk with an invalid user account
    def test_create_intentionalwalk_invalidaccount(self):

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

    # Test creation of a intentional walk with a missing field
    def test_create_intentionalwalk_missing_eventid(self):

        del self.request_params["intentional_walks"][0]["event_id"]

        # Send the request
        response = self.client.post(path=self.url, data=self.request_params, content_type=self.content_type)
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "error", msg=fail_message)
        self.assertEqual(
            response_data["message"], "Required input 'event_id' missing in the request", msg=fail_message,
        )

    # Test creation of a intentional walk with a missing field
    def test_create_intentionalwalk_missing_steps(self):

        del self.request_params["intentional_walks"][0]["steps"]

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
