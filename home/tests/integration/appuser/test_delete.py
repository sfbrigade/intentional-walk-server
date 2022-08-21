from django.core.exceptions import ObjectDoesNotExist
from django.test import Client, TestCase


class ApiTestCase(TestCase):
    def setUp(self):
        # Test client
        self.client = Client()

        # Urls for creation and deletion
        self.create_url = "/api/appuser/create"
        self.del_url = "/api/appuser/delete"
        self.content_type = "application/json"

        # Constants
        self.account_id1 = "12345"
        self.account_id2 = "23456"
        self.email1 = "john@blah.com"
        self.email2 = "joe@blah.com"

        # Request parameters
        base_params = {
            "name": "John Doe",
            "zip": "72185",
            "age": 99,
        }
        self.request_params1 = base_params.copy()
        self.request_params2 = base_params.copy()
        self.request_params1.update(
            {
                "name": "John Doe",
                "email": self.email1,
                "account_id": self.account_id1,
            }
        )
        self.request_params2.update(
            {
                "name": "Joe Doe",
                "email": self.email2,
                "account_id": self.account_id2,
            }
        )

        # Register the users
        self.create_user_and_confirm_response(self.request_params1)
        self.create_user_and_confirm_response(self.request_params2)

        self.existing_user_accts = [self.account_id1, self.account_id2]

    def tearDown(self) -> None:
        for acct_id in self.existing_user_accts:
            response = self.client.delete(
                path=self.del_url,
                data={"account_id": acct_id},
                content_type=self.content_type,
            )
            self.check_delete_success(response, self.account_id1)

    def create_user_and_confirm_response(self, request_params):
        # Create the user
        response = self.client.post(
            path=self.create_url,
            data=request_params,
            content_type=self.content_type,
        )

        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "success", msg=fail_message)

    def check_delete_success(self, response, deleted_account_id):
        # Check for a successful delete response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "success", msg=fail_message)
        self.assertEqual(
            response_data["message"],
            "Account deleted successfully",
            msg=fail_message,
        )

        # Check user/device no longer exists by trying & failing to
        # update the nonexistent user
        with self.assertRaises(ObjectDoesNotExist):
            self.client.put(
                path=self.create_url,
                data={"account_id": deleted_account_id},
                content_type=self.content_type,
            )

    def check_users_still_exist(self, valid_account_ids=[]):
        # Check other users still exist
        for acct_id in valid_account_ids:
            expected_success_update_response = self.client.put(
                path=self.create_url,
                data={"account_id": acct_id},
                content_type=self.content_type,
            )
            # Check for a successful response by the server
            self.assertEqual(expected_success_update_response.status_code, 200)
            # Parse the response
            response_data = expected_success_update_response.json()
            fail_message = f"Server response - {response_data}"
            self.assertEqual(
                response_data["status"], "success", msg=fail_message
            )
            self.assertEqual(
                response_data["message"],
                "Account updated successfully",
                msg=fail_message,
            )

    def test_delete_user_success(self):
        # Delete the first user
        response = self.client.delete(
            path=self.del_url,
            data={"account_id": self.account_id1},
            content_type=self.content_type,
        )

        self.check_delete_success(response, self.account_id1)
        self.check_users_still_exist([self.account_id2])

        self.existing_user_accts = [self.account_id2]

    def check_delete_failure(self, response, expected_msg):
        # Check for a failed delete response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "error", msg=fail_message)
        self.assertEqual(
            response_data["message"], expected_msg, msg=fail_message
        )

    def test_delete_user_failure_nonexistent(self):
        # Delete nonexistent user
        response = self.client.delete(
            path=self.del_url,
            data={"account_id": "fakeID"},
            content_type=self.content_type,
        )

        self.check_delete_failure(
            response,
            expected_msg="Cannot find user with specified account id.",
        )
        self.check_users_still_exist([self.account_id1, self.account_id2])

    def test_delete_user_failure_incorrect_params(self):
        # Send incorrect params
        response = self.client.delete(
            path=self.del_url,
            data={"what_is_this": self.account_id1},
            content_type=self.content_type,
        )

        self.check_delete_failure(
            response,
            expected_msg="Required input 'account_id' missing in the request",
        )
        self.check_users_still_exist([self.account_id1, self.account_id2])
