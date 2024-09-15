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
        self.url = "/api/v2/intentionalwalk"
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
                    "pause_time": 456,
                }
            ],
        }
        # Content type
        self.content_type = "application/json"

    # Test a successful creation of a intentional walk
    def test_create_intentionalwalk(self):

        # Send the request
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
            response_data["account_id"],
            self.request_params["account_id"],
            msg=fail_message,
        )
        self.assertEqual(
            response_data["intentional_walks"][0]["event_id"],
            self.request_params["intentional_walks"][0]["event_id"],
            msg=fail_message,
        )
        self.assertEqual(
            response_data["intentional_walks"][0]["start"],
            self.request_params["intentional_walks"][0]["start"],
            msg=fail_message,
        )
        self.assertEqual(
            response_data["intentional_walks"][0]["end"],
            self.request_params["intentional_walks"][0]["end"],
            msg=fail_message,
        )
        self.assertEqual(
            response_data["intentional_walks"][0]["steps"],
            self.request_params["intentional_walks"][0]["steps"],
            msg=fail_message,
        )
        self.assertEqual(
            response_data["intentional_walks"][0]["pause_time"],
            self.request_params["intentional_walks"][0]["pause_time"],
            msg=fail_message,
        )
        self.assertEqual(
            response_data["intentional_walks"][0]["distance"],
            self.request_params["intentional_walks"][0]["distance"],
            msg=fail_message,
        )

    # Test creation of a intentional walk with an invalid user account
    def test_create_intentionalwalk_invalidaccount(self):

        self.request_params["account_id"] = "0000000"

        # Send the request
        response = self.client.post(
            path=self.url,
            data=self.request_params,
            content_type=self.content_type,
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 404)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(
            response_data["detail"],
            "Unregistered device - "
            f'{self.request_params["account_id"]}. '
            "Please register first!",
            msg=fail_message,
        )

    # Test creation of a intentional walk with a missing steps field
    def test_create_intentionalwalk_missing_steps(self):

        del self.request_params["intentional_walks"][0]["steps"]

        # Send the request
        response = self.client.post(
            path=self.url,
            data=self.request_params,
            content_type=self.content_type,
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 422)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(
            response_data["detail"][0]["type"], "missing", msg=fail_message
        )
        self.assertIn(
            "steps", response_data["detail"][0]["loc"], msg=fail_message
        )
        self.assertEqual(
            response_data["detail"][0]["msg"],
            "Field required",
            msg=fail_message,
        )

    # Test creation of a intentional walk with a missing account_id field
    def test_create_intentionalwalk_missing_account_id(self):

        del self.request_params["account_id"]

        # Send the request
        response = self.client.post(
            path=self.url,
            data=self.request_params,
            content_type=self.content_type,
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 422)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(
            response_data["detail"][0]["type"], "missing", msg=fail_message
        )
        self.assertIn(
            "account_id", response_data["detail"][0]["loc"], msg=fail_message
        )
        self.assertEqual(
            response_data["detail"][0]["msg"],
            "Field required",
            msg=fail_message,
        )

    # Test creation of a intentional walk with a missing intentional_walks field
    def test_create_intentionalwalk_missing_intentional_walks(self):

        del self.request_params["intentional_walks"]

        # Send the request
        response = self.client.post(
            path=self.url,
            data=self.request_params,
            content_type=self.content_type,
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 422)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(
            response_data["detail"][0]["type"], "missing", msg=fail_message
        )
        self.assertIn(
            "intentional_walks",
            response_data["detail"][0]["loc"],
            msg=fail_message,
        )
        self.assertEqual(
            response_data["detail"][0]["msg"],
            "Field required",
            msg=fail_message,
        )

    # Test invalid method
    def test_create_intentionalwalk_invalid_methods(self):
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
