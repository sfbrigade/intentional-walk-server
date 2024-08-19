from django.test import Client, TestCase

from home.models import Device


class ApiTestCase(TestCase):
    def setUp(self):
        # Test client
        self.client = Client()

        self.account_id = "12345"

        # Create a user
        response = self.client.post(
            path="/api/v2/appuser",
            data={
                "name": "Abhay Kashyap",
                "email": "abhay@blah.com",
                "zip": "94102",
                "age": 99,
                "account_id": self.account_id,
            },
            content_type="application/json",
        )

        # Check for a successful response by the server
        self.assertEqual(response.status_code, 201)

        # device = Device.objects.get(device_id=self.account_id)
        # self.account = device.account

        # Details for Weekly Goal creation
        self.url = "/api/v2/weeklygoal"
        self.start_of_week = "2023-08-21"
        self.start_of_week_param = "2023-08-23"
        # Request parameters
        self.request_params = {
            "account_id": self.account_id,
            "weekly_goal": {
                "start_of_week": self.start_of_week_param,
                "steps": 2000,
                "days": 3,
            },
        }
        # Content type
        self.content_type = "application/json"

    # Test a successful creation of a weekly goal
    def test_create_weeklygoal(self):

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
            response_data["weekly_goal"]["start_of_week"],
            self.start_of_week,
            msg=fail_message,
        )
        self.assertEqual(
            response_data["weekly_goal"]["steps"],
            self.request_params["weekly_goal"]["steps"],
            msg=fail_message,
        )
        self.assertEqual(
            response_data["weekly_goal"]["days"],
            self.request_params["weekly_goal"]["days"],
            msg=fail_message,
        )

    # Test a successful update of a weekly goal where a weekly goal already exists
    def test_update_weeklygoal(self):

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
            response_data["weekly_goal"]["start_of_week"],
            self.start_of_week,
            msg=fail_message,
        )
        self.assertEqual(
            response_data["weekly_goal"]["steps"],
            self.request_params["weekly_goal"]["steps"],
            msg=fail_message,
        )
        self.assertEqual(
            response_data["weekly_goal"]["days"],
            self.request_params["weekly_goal"]["days"],
            msg=fail_message,
        )

        # change weekly_goal values
        self.request_params["weekly_goal"]["start_of_week"] = "2023-08-25"
        self.request_params["weekly_goal"]["steps"] = 50000
        self.request_params["weekly_goal"]["days"] = 7

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
            response_data["weekly_goal"]["start_of_week"],
            self.start_of_week,
            msg=fail_message,
        )
        self.assertEqual(
            response_data["weekly_goal"]["steps"],
            self.request_params["weekly_goal"]["steps"],
            msg=fail_message,
        )
        self.assertEqual(
            response_data["weekly_goal"]["days"],
            self.request_params["weekly_goal"]["days"],
            msg=fail_message,
        )

    # Test a creation of a weekly goal with an invalid user account
    def test_create_weeklygoal_invalid_account(self):
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
            f'{self.request_params["account_id"]}.'
            " Please register first!",
            msg=fail_message,
        )

    # Test a creation of a weekly goal with missing weekly_goal
    def test_create_weeklygoal_wihtout_weeklygoal(self):

        del self.request_params["weekly_goal"]

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
            "weekly_goal", response_data["detail"][0]["loc"], msg=fail_message
        )
        self.assertEqual(
            response_data["detail"][0]["msg"],
            "Field required",
            msg=fail_message,
        )

    # Test a creation of a weekly goal with missing weekly_goal field steps
    def test_create_weeklygoal_wihtout_weeklygoal_steps(self):

        del self.request_params["weekly_goal"]["steps"]

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

    # Test invalid methods
    def test_create_weeklygoal_invalid_methods(self):
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
