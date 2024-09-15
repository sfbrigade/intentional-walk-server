from django.test import Client, TestCase

from home.models import Account, Device


class ApiTestCase(TestCase):
    def setUp(self):
        # Test client
        self.client = Client()

        # Urls for creation and deletion
        self.appuser_url = "/api/v2/appuser"
        self.device_url = "/api/v2/device"
        self.content_type = "application/json"

        # Constants
        self.account_id1 = "12345"
        self.account_id2 = "23456"
        self.email1 = "john@blah.com"
        self.email2 = "joe@blah.com"

        # Request parameters
        base_params = {
            "name": "John Doe",
            "zip": "94132",
            "age": 99,
        }
        self.request_params_user1 = base_params.copy()
        self.request_params_user2 = base_params.copy()
        self.request_params_user1.update(
            {
                "name": "John Doe",
                "email": self.email1,
                "account_id": self.account_id1,
            }
        )
        self.request_params_user2.update(
            {
                "name": "Joe Doe",
                "email": self.email2,
                "account_id": self.account_id2,
            }
        )

        # Register the users
        self.create_user_and_device_confirm_response(self.request_params_user1)
        self.create_user_and_device_confirm_response(self.request_params_user2)

        self.existing_user_accts = [self.account_id1, self.account_id2]

    def tearDown(self) -> None:
        for acct_id in self.existing_user_accts:
            response = self.client.delete(
                path=f"{self.appuser_url}/{acct_id}",
                # data={"account_id": acct_id},
                content_type=self.content_type,
            )

            self.check_delete_success(response, acct_id)

    def create_user_and_device_confirm_response(self, request_params):
        # Create the user
        request_params = request_params.copy()
        device_id = request_params["account_id"]
        response = self.client.post(
            path=self.appuser_url,
            data=request_params,
            content_type=self.content_type,
        )

        # Check for a successful response by the server
        self.assertEqual(response.status_code, 201)

        # Check object was created and matches expected values
        user_obj = Account.objects.get(email=request_params["email"])
        del request_params["account_id"]
        for field, expected_value in request_params.items():
            self.assertEqual(
                getattr(user_obj, field), expected_value, msg=f"{field}"
            )

        # Required request params for updating device info
        request_params = {
            "device_model": "iPhone16,1",
            "manufacturer": "Apple",
            "os_name": "iOS",
            "os_version": "17.5",
            "device_id": device_id,
        }
        # Update the user's device for the first time
        response = self.client.put(
            path=f"{self.device_url}/{device_id}",
            data=request_params,
            content_type=self.content_type,
        )

        # Check for a successful response by the server
        self.assertEqual(response.status_code, 204)

        # Check for a successful update in the database
        device_obj = Device.objects.get(device_id=device_id)
        for field, value in request_params.items():
            self.assertEqual(
                getattr(device_obj, field),
                value,
                msg=f"field: {field} - Expected: {value} \
                        Got: {getattr(device_obj, field)}",
            )

    def check_delete_success(self, response, deleted_account_id):
        # Check for a successful delete response by the server
        self.assertEqual(response.status_code, 204, msg=response)

        # Check user/device no longer exists by trying & failing to
        # update the nonexistent user
        patch_response = self.client.patch(
            path=f"{self.appuser_url}/{deleted_account_id}",
            data={"account_id": deleted_account_id},
            content_type=self.content_type,
        )
        self.assertEqual(patch_response.status_code, 404, msg=patch_response)

        patch_response = self.client.patch(
            path=f"{self.device_url}/{deleted_account_id}",
            data={"device_id": deleted_account_id},
            content_type=self.content_type,
        )
        self.assertEqual(patch_response.status_code, 404, msg=patch_response)

    def check_users_and_device_still_exist(self, valid_account_ids=[]):
        # Check other users still exist
        for acct_id in valid_account_ids:
            # Update user
            expected_success_update_response = self.client.patch(
                path=f"{self.appuser_url}/{acct_id}",
                data={"account_id": acct_id},
                content_type=self.content_type,
            )
            # Check for a successful response by the server
            self.assertEqual(expected_success_update_response.status_code, 204)

            # Update device
            expected_success_update_response = self.client.patch(
                path=f"{self.device_url}/{acct_id}",
                data={"device_id": acct_id},
                content_type=self.content_type,
            )
            # Check for a successful response by the server
            self.assertEqual(expected_success_update_response.status_code, 204)

    def test_delete_device_success(self):
        # Delete the first user
        response = self.client.delete(
            path=f"{self.device_url}/{self.account_id1}",
            content_type=self.content_type,
        )

        self.check_delete_success(response, self.account_id1)
        self.check_users_and_device_still_exist([self.account_id2])

        self.existing_user_accts = [self.account_id2]

    def check_delete_failure(self, response, expected_msg):
        # Check for a failed delete response by the server
        self.assertEqual(response.status_code, 404)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(
            response_data["detail"], expected_msg, msg=fail_message
        )

    def test_delete_user_failure_nonexistent(self):
        # Delete nonexistent user
        response = self.client.delete(
            path=f"{self.device_url}/fakeID",
            content_type=self.content_type,
        )

        self.check_delete_failure(
            response,
            expected_msg="Unregistered device - device_id: fakeID. Please register first!",
        )
        self.check_users_and_device_still_exist(
            [self.account_id1, self.account_id2]
        )
