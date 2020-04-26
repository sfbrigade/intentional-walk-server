import datetime
from dateutil import parser
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

        # Create three intentional walks
        self.intentional_walks = {
            "account_id": "12345",
            "intentional_walks": [
                {"event_id": "1111", "start": "2020-02-21T12:15:00-05:00", "end": "2020-02-21T12:45:00-05:00",
                "steps": 1500, "distance": 1.3, "pause_time": 23.5},
                {"event_id": "2222", "start": "2020-02-21T15:20:00-05:00", "end": "2020-02-21T15:50:00-05:00",
                "steps": 500, "distance": 0.4, "pause_time": 53.5},
                {"event_id": "3333", "start": "2020-02-22T13:15:00-05:00", "end": "2020-02-22T13:45:00-05:00",
                "steps": 1000, "distance": 0.7, "pause_time": 100.1},
            ]
        }
        # Create intentional walks
        response = self.client.post(path="/api/intentionalwalk/create", data=self.intentional_walks, content_type="application/json",)
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "success", msg=fail_message)
        self.assertEqual(response_data["message"], "Intentional Walks recorded successfully", msg=fail_message)

        # Details for intentional walk list view
        self.url = "/api/intentionalwalk/get"
        # Request parameters
        self.request_params = {"account_id": "12345"}
        # Content type
        self.content_type = "application/json"

    def test_intentionalwalk_get_failure(self):
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

    def test_intentionalwalk_get(self):
        response = self.client.post(path=self.url, data=self.request_params, content_type=self.content_type)
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "success", msg=fail_message)
        self.assertIn("intentional_walks", response_data, msg=fail_message)
        self.assertIn("total_steps", response_data, msg=fail_message)
        self.assertIn("total_distance", response_data, msg=fail_message)
        self.assertIn("total_walk_time", response_data, msg=fail_message)
        self.assertIn("total_pause_time", response_data, msg=fail_message)
        for walk in response_data["intentional_walks"]:
            self.assertIn("start", walk, msg=fail_message)
            self.assertIn("end", walk, msg=fail_message)
            self.assertIn("steps", walk, msg=fail_message)
            self.assertIn("distance", walk, msg=fail_message)
            self.assertIn("walk_time", walk, msg=fail_message)
            self.assertIn("pause_time", walk, msg=fail_message)
        # Check if total steps is correct
        self.assertEqual(response_data["total_steps"], sum([dw["steps"] for dw in self.intentional_walks["intentional_walks"]]), msg=fail_message)
        self.assertEqual(response_data["total_distance"], sum([dw["distance"] for dw in self.intentional_walks["intentional_walks"]]), msg=fail_message)
        self.assertEqual(response_data["total_pause_time"], sum([dw["pause_time"] for dw in self.intentional_walks["intentional_walks"]]), msg=fail_message)
        self.assertEqual(response_data["total_walk_time"], sum([(parser.parse(dw["end"]) - parser.parse(dw["start"])).total_seconds() - dw["pause_time"]
                                                           for dw in self.intentional_walks["intentional_walks"]]),
                         msg=fail_message)
        # Check if the number of events match
        self.assertEqual(len(response_data["intentional_walks"]), len(self.intentional_walks["intentional_walks"]), msg=fail_message)

        # Check if they have the same exact data
        # Remove timestamp strings since formatting is different
        self.assertEqual(
            [{"steps": dw["steps"], "distance": dw["distance"], "pause_time": dw["pause_time"]}
             for dw in sorted(response_data["intentional_walks"], key=lambda x: x["start"], reverse=True)],
            [{"steps": dw["steps"], "distance": dw["distance"], "pause_time": dw["pause_time"]}
             for dw in sorted(self.intentional_walks["intentional_walks"], key=lambda x: x["start"], reverse=True)],
            msg=fail_message,
        )

    # Check if walks across multiple accounts tied to the same email are aggregated
    def test_intentionalwalk_get_aggregated(self):

        # Create a second account from a different device but with the same email
        response = self.client.post(
            path="/api/appuser/create",
            data={
                "name": "Abhay Kashyap",
                "email": "abhay@blah.com",
                "zip": "72185",
                "age": 99,
                "account_id": "54321",
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

        # Create a third account from a different device but with the same email
        response = self.client.post(
            path="/api/appuser/create",
            data={
                "name": "Abhay Kashyap",
                "email": "abhay@blah.com",
                "zip": "72185",
                "age": 99,
                "account_id": "99999",
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


        # Create additional walks
        new_intentional_walks = {
            "account_id": "54321",
            "intentional_walks": [
                {"event_id": "4444", "start": "2020-02-21T18:15:00-05:00", "end": "2020-02-21T18:45:00-05:00",
                "steps": 700, "distance": 0.7, "pause_time": 600},
                {"event_id": "8888", "start": "2020-02-23T15:20:00-05:00", "end": "2020-02-23T15:50:00-05:00",
                "steps": 900, "distance": 0.8, "pause_time": 400},
            ]
        }
        self.intentional_walks["intentional_walks"] += new_intentional_walks["intentional_walks"]
        response = self.client.post(path="/api/intentionalwalk/create", data=new_intentional_walks, content_type="application/json",)
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "success", msg=fail_message)
        self.assertEqual(response_data["message"], "Intentional Walks recorded successfully", msg=fail_message)

        new_intentional_walks = {
            "account_id": "99999",
            "intentional_walks": [
                {"event_id": "9999", "start": "2020-02-24T13:15:00-05:00", "end": "2020-02-22T13:45:00-05:00",
                "steps": 1000, "distance": 1.1, "pause_time": 600.5},
            ]
        }
        self.intentional_walks["intentional_walks"] += new_intentional_walks["intentional_walks"]
        response = self.client.post(path="/api/intentionalwalk/create", data=new_intentional_walks, content_type="application/json",)
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "success", msg=fail_message)
        self.assertEqual(response_data["message"], "Intentional Walks recorded successfully", msg=fail_message)


        response = self.client.post(path=self.url, data=self.request_params, content_type=self.content_type)
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "success", msg=fail_message)
        self.assertIn("intentional_walks", response_data, msg=fail_message)
        self.assertIn("total_steps", response_data, msg=fail_message)
        self.assertIn("total_distance", response_data, msg=fail_message)
        self.assertIn("total_walk_time", response_data, msg=fail_message)
        self.assertIn("total_pause_time", response_data, msg=fail_message)
        for walk in response_data["intentional_walks"]:
            self.assertIn("start", walk, msg=fail_message)
            self.assertIn("end", walk, msg=fail_message)
            self.assertIn("steps", walk, msg=fail_message)
            self.assertIn("distance", walk, msg=fail_message)
            self.assertIn("walk_time", walk, msg=fail_message)
            self.assertIn("pause_time", walk, msg=fail_message)
        # Check if total steps is correct
        self.assertEqual(response_data["total_steps"], sum([dw["steps"] for dw in self.intentional_walks["intentional_walks"]]), msg=fail_message)
        self.assertEqual(response_data["total_distance"], sum([dw["distance"] for dw in self.intentional_walks["intentional_walks"]]), msg=fail_message)
        self.assertEqual(response_data["total_pause_time"], sum([dw["pause_time"] for dw in self.intentional_walks["intentional_walks"]]), msg=fail_message)
        self.assertEqual(response_data["total_walk_time"], sum([(parser.parse(dw["end"]) - parser.parse(dw["start"])).total_seconds() - dw["pause_time"]
                                                           for dw in self.intentional_walks["intentional_walks"]]),
                         msg=fail_message)
        # Check if the number of events match
        self.assertEqual(len(response_data["intentional_walks"]), len(self.intentional_walks["intentional_walks"]), msg=fail_message)

        # Check if they have the same exact data
        # Remove timestamp strings since formatting is different
        self.assertEqual(
            [{"steps": dw["steps"], "distance": dw["distance"], "pause_time": dw["pause_time"]}
             for dw in sorted(response_data["intentional_walks"], key=lambda x: x["start"], reverse=True)],
            [{"steps": dw["steps"], "distance": dw["distance"], "pause_time": dw["pause_time"]}
             for dw in sorted(self.intentional_walks["intentional_walks"], key=lambda x: x["start"], reverse=True)],
            msg=fail_message,
        )
