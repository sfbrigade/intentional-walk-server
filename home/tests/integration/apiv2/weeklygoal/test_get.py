from django.forms.models import model_to_dict
from django.test import Client, TestCase

from home.models import Device, WeeklyGoal


class ApiTestCase(TestCase):
    def setUp(self):
        # Test client
        self.client = Client()

        self.email = "abhay@blah.com"
        self.account_id = "12345"

        # Create a user
        response = self.client.post(
            path="/api/v2/appuser",
            data={
                "name": "Abhay Kashyap",
                "email": self.email,
                "zip": "94102",
                "age": 99,
                "account_id": self.account_id,
            },
            content_type="application/json",
        )

        # Check for a successful response by the server
        self.assertEqual(response.status_code, 201)

        device = Device.objects.get(device_id=self.account_id)
        self.account = device.account

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
        self.url = "/api/v2/weeklygoal"
        # Request parameters
        self.request_params = {"account_id": self.account_id}

    # Test a successful request for weekly goals
    def test_weeklygoal_get_success(self):
        # Send the request
        response = self.client.get(
            path=f"{self.url}/{self.request_params['account_id']}"
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200, msg=f"{response.content}")
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertIn("weekly_goals", response_data, msg=fail_message)
        i = 2
        for goal in response_data["weekly_goals"]:
            goalDict = model_to_dict(self.weekly_goals[i])
            goalDict["account_id"] = goalDict.get("account")
            del goalDict["account"]
            self.assertEqual(goal, goalDict)
            i -= 1

    # Test getting weekly goals from an account that doesn't exist
    def test_weeklygoal_get_failure_invalid_account(self):
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
            "Unregistered account - "
            f'{self.request_params["account_id"]}.'
            " Please register first!",
            msg=fail_message,
        )

    # Test getting weekly goals with missing account id param
    def test_weeklygoal_get_failure_missing_account_id(self):
        del self.request_params["account_id"]

        # Send the request
        response = self.client.get(
            path=f"{self.url}/",
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 404)
        # Parse the response
        response_data = response.content
        fail_message = f"Server response - {response_data}"
        self.assertIn(b"Not Found", response_data, msg=fail_message)

    # # Test invalid methods
    # def test_weeklygoal_get_invalid_methods(self):
    #     # Test not allowed get method
    #     response = self.client.get(
    #         path=self.url,
    #         data=self.request_params,
    #         content_type=self.content_type,
    #     )
    #     # Check for a successful response by the server
    #     self.assertEqual(response.status_code, 200)
    #     # Parse the response
    #     response_data = response.json()
    #     fail_message = f"Server response - {response_data}"
    #     self.assertEqual(response_data["status"], "error", msg=fail_message)
    #     self.assertEqual(
    #         response_data["message"],
    #         "Method not allowed!",
    #         msg=fail_message,
    #     )

    #     # Test not allowed patch method
    #     response = self.client.patch(
    #         path=self.url,
    #         data=self.request_params,
    #         content_type=self.content_type,
    #     )
    #     # Check for a successful response by the server
    #     self.assertEqual(response.status_code, 200)
    #     # Parse the response
    #     response_data = response.json()
    #     fail_message = f"Server response - {response_data}"
    #     self.assertEqual(response_data["status"], "error", msg=fail_message)
    #     self.assertEqual(
    #         response_data["message"],
    #         "Method not allowed!",
    #         msg=fail_message,
    #     )

    #     # Test not allowed put method
    #     response = self.client.put(
    #         path=self.url,
    #         data=self.request_params,
    #         content_type=self.content_type,
    #     )
    #     # Check for a successful response by the server
    #     self.assertEqual(response.status_code, 200)
    #     # Parse the response
    #     response_data = response.json()
    #     fail_message = f"Server response - {response_data}"
    #     self.assertEqual(response_data["status"], "error", msg=fail_message)
    #     self.assertEqual(
    #         response_data["message"],
    #         "Method not allowed!",
    #         msg=fail_message,
    #     )

    #     # Test not allowed delete method
    #     response = self.client.delete(
    #         path=self.url,
    #         data=self.request_params,
    #         content_type=self.content_type,
    #     )
    #     # Check for a successful response by the server
    #     self.assertEqual(response.status_code, 200)
    #     # Parse the response
    #     response_data = response.json()
    #     fail_message = f"Server response - {response_data}"
    #     self.assertEqual(response_data["status"], "error", msg=fail_message)
    #     self.assertEqual(
    #         response_data["message"],
    #         "Method not allowed!",
    #         msg=fail_message,
    #     )
