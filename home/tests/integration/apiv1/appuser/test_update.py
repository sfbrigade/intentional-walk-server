from django.test import Client, TestCase

from home.models import Account


class ApiTestCase(TestCase):
    def setUp(self):
        # Test client
        self.client = Client()
        # Url for creation
        self.url = "/api/appuser/create"
        # Constants
        self.account_id = "12345"
        self.email = "john@blah.com"
        # Request parameters
        self.request_params = {
            "name": "John Doe",
            "email": self.email,
            "zip": "72185",
            "age": 99,
            "account_id": self.account_id,
        }
        # Content type
        self.content_type = "application/json"

        # Register the user
        response = self.client.post(
            path=self.url,
            data=self.request_params,
            content_type=self.content_type,
        )

        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "success", msg=fail_message)

    # Test updating a User's demographics
    # First user screen (name, email, age) registers a user
    # Additional demographics update with PUT. Test applies to these changes.
    def test_update_appuser_demographics(self):

        # UPDATE USER DEMOGRAPHICS
        request_params = {
            "account_id": self.account_id,
            "is_latino": "YE",
        }

        # Register the user
        response = self.client.put(
            path=self.url, data=request_params, content_type=self.content_type
        )

        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "success", msg=fail_message)
        self.assertEqual(
            response_data["message"],
            "Account updated successfully",
            msg=fail_message,
        )
        user_obj = Account.objects.get(email=self.email)

        field = "is_latino"
        self.assertEqual(
            getattr(user_obj, field), request_params[field], msg=fail_message
        )

        request_params = {
            "account_id": self.account_id,
            "gender": "TM",
            "gender_other": None,
            "race": ["BL", "OT"],
            "race_other": "Some other race",
            "sexual_orien": "DA",
            "sexual_orien_other": None,
        }

        response = self.client.put(
            path=self.url, data=request_params, content_type=self.content_type
        )
        self.assertEqual(response.status_code, 200)
        user_obj = Account.objects.get(email=self.email)

        for field in [
            "gender",
            "gender_other",
            "race_other",
            "sexual_orien",
            "sexual_orien_other",
        ]:
            self.assertEqual(
                getattr(user_obj, field),
                request_params[field],
                msg=fail_message,
            )
        self.assertSetEqual(
            set(user_obj.race), set(request_params["race"]), msg=fail_message
        )

    # Test updating a User's age
    # This would hit the same creation URL
    def test_update_appuser_age(self):
        # UPDATE THE USERS AGE
        request_params = {**self.request_params, "age": 88}

        # Send the update
        response = self.client.post(
            path=self.url, data=request_params, content_type=self.content_type
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "success", msg=fail_message)
        self.assertEqual(
            response_data["message"],
            "Device & account updated successfully",
            msg=fail_message,
        )
        self.assertEqual(
            response_data["payload"]["account_id"],
            request_params["account_id"],
            msg=fail_message,
        )
        user_obj = Account.objects.get(email=self.email)
        for field in ["name", "email", "zip", "age"]:
            self.assertEqual(
                getattr(user_obj, field),
                request_params[field],
                msg=fail_message,
            )

    # Test updating a User's name
    # This would hit the same creation URL
    def test_update_appuser_name(self):
        # UPDATE THE USERS NAME
        request_params = {**self.request_params, "name": "Abhay"}

        # Send the update
        response = self.client.post(
            path=self.url, data=request_params, content_type=self.content_type
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "success", msg=fail_message)
        self.assertEqual(
            response_data["message"],
            "Device & account updated successfully",
            msg=fail_message,
        )
        self.assertEqual(
            response_data["payload"]["account_id"],
            request_params["account_id"],
            msg=fail_message,
        )
        user_obj = Account.objects.get(email=self.email)
        for field in ["name", "email", "zip", "age"]:
            self.assertEqual(
                getattr(user_obj, field),
                request_params[field],
                msg=fail_message,
            )

    # Test updating a User's email
    # This shouldn't update
    def test_update_appuser_email(self):
        # UPDATE THE USERS EMAIL
        request_params = {
            **self.request_params,
            "email": "abhaykashyap@blah.com",
        }

        # Register the user first
        response = self.client.post(
            path=self.url, data=request_params, content_type=self.content_type
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "error", msg=fail_message)
        self.assertEqual(
            response_data["message"],
            "Email cannot be updated. Contact admin",
            msg=fail_message,
        )

    # Test updating User's age without providing account_id
    # This should return a response with status "error" and a fail message
    def test_update_appuser_missing_account_id(self):
        # Required fields for user creation
        # Remove the account_id field
        request_params = {**self.request_params, "age": 88}
        del request_params["account_id"]

        # Register the user
        response = self.client.put(
            path=self.url, data=request_params, content_type=self.content_type
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "error", msg=fail_message)
        self.assertEqual(
            response_data["message"],
            "Required input 'account_id' missing in the request",
            msg=fail_message,
        )

    # Test invalid method - patch
    def test_update_appuser_invalid_methods(self):
        # Required fields for user creation
        request_params = {**self.request_params, "age": 88}

        # Test get method
        response = self.client.get(
            path=self.url, data=request_params, content_type=self.content_type
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "error", msg=fail_message)
        self.assertEqual(
            response_data["message"],
            "Method not allowed!",
            msg=fail_message,
        )

        # Test patch method
        response = self.client.patch(
            path=self.url, data=request_params, content_type=self.content_type
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "error", msg=fail_message)
        self.assertEqual(
            response_data["message"],
            "Method not allowed!",
            msg=fail_message,
        )

        # Test delete method
        response = self.client.delete(
            path=self.url, data=request_params, content_type=self.content_type
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "error", msg=fail_message)
        self.assertEqual(
            response_data["message"],
            "Method not allowed!",
            msg=fail_message,
        )
