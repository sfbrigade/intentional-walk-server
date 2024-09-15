from django.test import Client, TestCase

from home.models import Account


class ApiTestCase(TestCase):
    def setUp(self):
        # Test client
        self.client = Client()
        # Url for creation
        self.url = "/api/v2/appuser"
        # Request parameters
        self.request_params = {
            "name": "John Doe",
            "email": "john@blah.com",
            "zip": "94105",
            "age": 99,
            "account_id": "12345",
        }
        self.expected_response = {
            "name": "John Doe",
            "email": "john@blah.com",
            "zip": "94105",
            "age": 99,
            "is_tester": False,
            "is_sf_resident": True,
        }
        # Content type
        self.content_type = "application/json"

    # Test creation of a new app user
    def test_create_appuser_success(self):
        # Register the user
        response = self.client.post(
            path=self.url,
            data=self.request_params,
            content_type=self.content_type,
        )

        # Check for a successful response by the server
        self.assertEqual(response.status_code, 201)
        # Check object was created and matches expected values
        user_obj = Account.objects.get(email=self.request_params["email"])

        for field, expected_value in self.expected_response.items():
            self.assertEqual(
                getattr(user_obj, field), expected_value, msg=f"{field}"
            )

    # Test creation of a new "Tester" app user
    def test_create_tester_appuser_success(self):
        # Set up request and response for a Tester user based in SF
        request_params = self.request_params.copy()
        request_params.update(
            {
                "name": "IWT John",
                "zip": "94105",
            }
        )
        expected_response = self.expected_response.copy()
        expected_response.update(
            {
                "name": "IWT John",
                "zip": "94105",
                "is_tester": True,
                "is_sf_resident": True,
            }
        )

        # Register the user
        response = self.client.post(
            path=self.url, data=request_params, content_type=self.content_type
        )

        # Check for a successful response by the server
        self.assertEqual(response.status_code, 201)
        # Check object was created and matches expected values
        user_obj = Account.objects.get(email=request_params["email"])

        for field, expected_value in expected_response.items():
            self.assertEqual(
                getattr(user_obj, field), expected_value, msg=f"{field}"
            )

    # Test creation of a duplicate user
    # This should default to an update
    def test_create_appuser_duplicate(self):
        # Register the user first
        response = self.client.post(
            path=self.url,
            data=self.request_params,
            content_type=self.content_type,
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 201)

        # Check object was created and matches expected values
        user_obj = Account.objects.get(email=self.request_params["email"])
        for field in ["name", "email", "zip", "age"]:
            self.assertEqual(
                getattr(user_obj, field),
                self.request_params[field],
                msg=f"{field}",
            )

        # Create the same user again
        # Create the same user but with different case email
        # This should NOT create a new user record
        request_params = {**self.request_params, "email": "John@blah.com"}

        # This should default to an UPDATE
        response = self.client.post(
            path=self.url,
            data=request_params,
            content_type=self.content_type,
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 201)

        # Check object was updated and matches expected values
        dupe_user_obj = Account.objects.get(
            email__iexact=request_params["email"]
        )
        for field in ["name", "zip", "age"]:
            self.assertEqual(
                getattr(dupe_user_obj, field),
                request_params[field],
                msg=f"{field}",
            )
        self.assertEqual(user_obj.id, dupe_user_obj.id)

    # Test creation of the same user using a different device
    # This should create a new account with the same email
    def test_create_appuser_new_device(self):

        # Register the user first
        response = self.client.post(
            path=self.url,
            data=self.request_params,
            content_type=self.content_type,
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 201)

        user_obj = Account.objects.get(email=self.request_params["email"])
        for field in ["name", "email", "zip", "age"]:
            self.assertEqual(
                getattr(user_obj, field),
                self.request_params[field],
                msg=f"{field}",
            )

        # Create the same user but with a different account id
        # This should NOT create a new user
        request_params = {
            **self.request_params,
            "email": "John@blah.com",
            "account_id": "54321",
        }

        # Register the user first
        response = self.client.post(
            path=self.url, data=request_params, content_type=self.content_type
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 201)

        # Check object was updated and matches expected values
        dupe_user_obj = Account.objects.get(
            email__iexact=request_params["email"]
        )
        for field in ["name", "zip", "age"]:
            self.assertEqual(
                getattr(dupe_user_obj, field),
                request_params[field],
            )
        self.assertEqual(dupe_user_obj.id, user_obj.id)

    # Test failure while create a new app with missing information
    def test_create_appuser_failure_missing_field_age(self):
        # Required fields for user creation
        # Remove the age field
        request_params = self.request_params.copy()
        del request_params["age"]

        # Register the user
        response = self.client.post(
            path=self.url, data=request_params, content_type=self.content_type
        )
        # Check for a response by the server
        self.assertEqual(response.status_code, 422)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(
            response_data["detail"][0]["type"], "missing", msg=fail_message
        )
        self.assertIn(
            "age", response_data["detail"][0]["loc"], msg=fail_message
        )
        self.assertEqual(
            response_data["detail"][0]["msg"],
            "Field required",
            msg=fail_message,
        )

    # Test failure while create a new app with missing information
    def test_create_appuser_failure_missing_field_device_id(self):
        # Required fields for user creation
        # Remove the account_id field
        request_params = self.request_params.copy()
        del request_params["account_id"]

        # Register the user
        response = self.client.post(
            path=self.url, data=request_params, content_type=self.content_type
        )
        # Check for a response by the server
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

    # Test invalid method
    def test_create_appuser_invalid_method(self):
        # Required fields for user creation
        request_params = self.request_params.copy()

        # Test not allowed get method
        response = self.client.get(
            path=self.url, data=request_params, content_type=self.content_type
        )
        # Check for a response by the server
        self.assertEqual(response.status_code, 405)
        # Parse the response
        response_data = response.content
        fail_message = f"Server response - {response_data}"
        self.assertEqual(
            response_data, b"Method not allowed", msg=fail_message
        )

        # Test not allowed patch method
        response = self.client.patch(
            path=self.url, data=request_params, content_type=self.content_type
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
            data=request_params["account_id"],
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
