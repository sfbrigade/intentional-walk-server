from django.test import Client, TestCase

from home.models import WeeklyGoal, Account


class ApiTestCase(TestCase):
    def setUp(self):
        # Test client
        self.client = Client()

        self.account_id = "12345"
        self.email = "abhay@blah.com"

        # Create a user
        response = self.client.post(
            path="/api/appuser/create",
            data={
                "name": "Abhay Kashyap",
                "email": self.email,
                "zip": "72185",
                "age": 99,
                "account_id": self.account_id,
            },
            content_type="application/json",
        )

        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()

        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "success", msg=fail_message)
        self.assertEqual(
            response_data["message"],
            "Device registered & account registered successfully",
            msg=fail_message,
        )

        self.account = Account.objects.get(email=self.email)

        # Define weekly goals
        self.weekly_goals = [
            WeeklyGoal(
                account=self.account,
                start_of_week="2023-08-21",
                steps=3,
                days=2000,
            ),
            WeeklyGoal(
                account=self.account,
                start_of_week="2023-08-27",
                steps=4,
                days=2500,
            ),
            WeeklyGoal(
                account=self.account,
                start_of_week="2023-09-04",
                steps=5,
                days=3000,
            ),
        ]

        # Create weekly goals
        response = WeeklyGoal.objects.bulk_create(self.weekly_goals)

        i = 0
        # Check for a successful response by the server
        for item in response:
            self.assertEqual(item, self.weekly_goals[i])
            i += 1

        # Details for intentional walk list view
        self.url = "/api/weeklygoal/get"
        # Request parameters
        # Content type
        self.content_type = "application/json"
        self.request_params = {"account_id": self.account_id}

    # Test a successful request for weekly goals
    def test_weeklygoal_get_success(self):
        # Send the request
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
        self.assertEqual(response_data["status"], "error", msg=fail_message)

    # Test getting weekly goals from an account that doesn't exist
    def test_weeklygoal_get_failure_invalid_account(self):
        self.request_params["account_id"] = "0000000"

        # Send the request
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
        self.assertEqual(response_data["status"], "error", msg=fail_message)
        self.assertEqual(
            response_data["message"],
            "Unregistered account - "
            f'{self.request_params["account_id"]}.'
            " Please register first!",
            msg=fail_message,
        )

    # Test getting weekly goals with missing account id param
    def test_weeklygoal_get_failure_missing_account_id(self):
        del self.request_params["account_id"]

        # Send the request
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
        self.assertEqual(response_data["status"], "error", msg=fail_message)
        self.assertEqual(
            response_data["message"],
            "Required input 'account_id' missing in the request",
            msg=fail_message,
        )
