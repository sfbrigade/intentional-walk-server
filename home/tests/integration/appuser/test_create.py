from django.test import Client, TestCase

from home.models import Account


class ApiTestCase(TestCase):
    def setUp(self):
        # Test client
        self.client = Client()
        # Url for creation
        self.url = "/api/appuser/create"
        # Request parameters
        self.request_params = {
            "name": "John Doe",
            "email": "john@blah.com",
            "zip": "72185",
            "age": 99,
            "account_id": "12345",
        }
        # Content type
        self.content_type = "application/json"

    # Test creation of a new app user
    def test_create_appuser_success(self):

        # Register the user
        response = self.client.post(path=self.url, data=self.request_params, content_type=self.content_type)

        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "success", msg=fail_message)
        self.assertEqual(
            response_data["message"], "Device registered & account registered successfully", msg=fail_message
        )
        self.assertEqual(
            response_data["payload"]["account_id"], self.request_params["account_id"], msg=fail_message,
        )
        user_obj = Account.objects.get(email=self.request_params["email"])
        for field in ["name", "email", "zip", "age"]:
            self.assertEqual(getattr(user_obj, field), self.request_params[field], msg=f"{field}")

    # Test creation of a duplicate user
    # This should default to an update
    def test_create_appuser_duplicate(self):

        # Register the user first
        response = self.client.post(path=self.url, data=self.request_params, content_type=self.content_type)
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "success", msg=fail_message)
        self.assertEqual(
            response_data["message"], "Device registered & account registered successfully", msg=fail_message
        )
        self.assertEqual(
            response_data["payload"]["account_id"], self.request_params["account_id"], msg=fail_message,
        )
        user_obj = Account.objects.get(email=self.request_params["email"])
        for field in ["name", "email", "zip", "age"]:
            self.assertEqual(getattr(user_obj, field), self.request_params[field], msg=f"{field}")


        # Create the same user again
        # This should default to an UPDATE
        response = self.client.post(path=self.url, data=self.request_params, content_type=self.content_type)
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "success", msg=fail_message)
        self.assertEqual(response_data["message"], "Device & account updated successfully", msg=fail_message)
        self.assertEqual(
            response_data["payload"]["account_id"], self.request_params["account_id"], msg=fail_message,
        )
        user_obj = Account.objects.get(email=self.request_params["email"])
        for field in ["name", "email", "zip", "age"]:
            self.assertEqual(getattr(user_obj, field), self.request_params[field], msg=f"{field}")

    # Test creation of the same user using a different device
    # This should create a new account with the same email
    def test_create_appuser_new_device(self):

        # Register the user first
        response = self.client.post(path=self.url, data=self.request_params, content_type=self.content_type)
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "success", msg=fail_message)
        self.assertEqual(
            response_data["message"], "Device registered & account registered successfully", msg=fail_message
        )
        self.assertEqual(
            response_data["payload"]["account_id"], self.request_params["account_id"], msg=fail_message,
        )
        user_obj = Account.objects.get(email=self.request_params["email"])
        for field in ["name", "email", "zip", "age"]:
            self.assertEqual(getattr(user_obj, field), self.request_params[field], msg=f"{field}")

        # Create the same user but with a different account id
        # This should create a new user
        request_params = {**self.request_params, "account_id": "54321"}

        # Register the user first
        response = self.client.post(path=self.url, data=request_params, content_type=self.content_type)
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "success", msg=fail_message)
        self.assertEqual(response_data["message"], "Device registered & account updated successfully", msg=fail_message)
        self.assertEqual(
            response_data["payload"]["account_id"], request_params["account_id"], msg=fail_message,
        )
        user_obj = Account.objects.get(email=request_params["email"])
        for field in ["name", "email", "zip", "age"]:
            self.assertEqual(getattr(user_obj, field), request_params[field], msg=fail_message)

    # Test failure while create a new app with missing information
    def test_create_appuser_failure_missing_field_age(self):
        # Required fields for user creation
        # Remove the age field
        request_params = self.request_params.copy()
        del request_params["age"]

        # Register the user
        response = self.client.post(path=self.url, data=request_params, content_type=self.content_type)
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "error", msg=fail_message)
        self.assertEqual(
            response_data["message"], "Required input 'age' missing in the request", msg=fail_message,
        )

    # Test failure while create a new app with missing information
    def test_create_appuser_failure_missing_field_device_id(self):
        # Required fields for user creation
        # Remove the account_id field
        request_params = self.request_params.copy()
        del request_params["account_id"]

        # Register the user
        response = self.client.post(path=self.url, data=request_params, content_type=self.content_type)
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "error", msg=fail_message)
        self.assertEqual(
            response_data["message"], "Required input 'account_id' missing in the request", msg=fail_message,
        )
