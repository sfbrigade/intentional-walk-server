import datetime
from django.test import Client, TestCase
from freezegun import freeze_time

from home.models import Contest


class ApiTestCase(TestCase):
    def setUp(self):
        # Test client
        self.client = Client()
        # Details for intentional walk list view
        self.url = "/api/contest/current"
        # Content type
        self.content_type = "application/json"

    def test_contest_current_error(self):
        # Send the request
        response = self.client.get(path=self.url, content_type=self.content_type)
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 200)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(response_data["status"], "error", msg=fail_message)
        self.assertEqual(
            response_data["message"], f"There are no contests", msg=fail_message,
        )

    def test_contest_current(self):
        # create a few contests
        contest1 = Contest()
        contest1.start_baseline = "2020-04-01"
        contest1.start_promo = "2020-04-24"
        contest1.start = "2020-05-01"
        contest1.end = "2020-05-31"
        contest1.save()

        contest2 = Contest()
        contest2.start_baseline = "2020-06-01"
        contest2.start_promo = "2020-06-21"
        contest2.start = "2020-07-01"
        contest2.end = "2020-07-31"
        contest2.save()

        # before first promo starts, failure
        with freeze_time("2020-04-01"):
            response = self.client.get(path=self.url, content_type=self.content_type)
            # Check for a successful response by the server
            self.assertEqual(response.status_code, 200)
            # Parse the response
            response_data = response.json()
            fail_message = f"Server response - {response_data}"
            self.assertEqual(response_data["status"], "error", msg=fail_message)
            self.assertEqual(
                response_data["message"], f"There are no contests", msg=fail_message,
            )

        # after promo starts for first contest
        with freeze_time("2020-04-28"):
            response = self.client.get(path=self.url, content_type=self.content_type)
            # Check for a successful response by the server
            self.assertEqual(response.status_code, 200)
            # Parse the response
            response_data = response.json()
            fail_message = f"Server response - {response_data}"
            self.assertEqual(response_data["status"], "success", msg=fail_message)
            self.assertEqual(response_data["payload"]["contest_id"], str(contest1.pk))
            self.assertEqual(response_data["payload"]["start_promo"], "2020-04-24")
            self.assertEqual(response_data["payload"]["start"], "2020-05-01")
            self.assertEqual(response_data["payload"]["end"], "2020-05-31")

        # during first contest
        with freeze_time("2020-05-15"):
            response = self.client.get(path=self.url, content_type=self.content_type)
            # Check for a successful response by the server
            self.assertEqual(response.status_code, 200)
            # Parse the response
            response_data = response.json()
            fail_message = f"Server response - {response_data}"
            self.assertEqual(response_data["status"], "success", msg=fail_message)
            self.assertEqual(response_data["payload"]["contest_id"], str(contest1.pk))
            self.assertEqual(response_data["payload"]["start_promo"], "2020-04-24")
            self.assertEqual(response_data["payload"]["start"], "2020-05-01")
            self.assertEqual(response_data["payload"]["end"], "2020-05-31")

        # after first contest, before promo starts for next
        with freeze_time("2020-06-14"):
            response = self.client.get(path=self.url, content_type=self.content_type)
            # Check for a successful response by the server
            self.assertEqual(response.status_code, 200)
            # Parse the response
            response_data = response.json()
            fail_message = f"Server response - {response_data}"
            self.assertEqual(response_data["status"], "success", msg=fail_message)
            self.assertEqual(response_data["payload"]["contest_id"], str(contest1.pk))
            self.assertEqual(response_data["payload"]["start_promo"], "2020-04-24")
            self.assertEqual(response_data["payload"]["start"], "2020-05-01")
            self.assertEqual(response_data["payload"]["end"], "2020-05-31")

        # after promo starts for next
        with freeze_time("2020-06-28"):
            response = self.client.get(path=self.url, content_type=self.content_type)
            # Check for a successful response by the server
            self.assertEqual(response.status_code, 200)
            # Parse the response
            response_data = response.json()
            fail_message = f"Server response - {response_data}"
            self.assertEqual(response_data["status"], "success", msg=fail_message)
            self.assertEqual(response_data["payload"]["contest_id"], str(contest2.pk))
            self.assertEqual(response_data["payload"]["start_promo"], "2020-06-21")
            self.assertEqual(response_data["payload"]["start"], "2020-07-01")
            self.assertEqual(response_data["payload"]["end"], "2020-07-31")

        # after last contest
        with freeze_time("2020-08-14"):
            response = self.client.get(path=self.url, content_type=self.content_type)
            # Check for a successful response by the server
            self.assertEqual(response.status_code, 200)
            # Parse the response
            response_data = response.json()
            fail_message = f"Server response - {response_data}"
            self.assertEqual(response_data["status"], "success", msg=fail_message)
            self.assertEqual(response_data["payload"]["contest_id"], str(contest2.pk))
            self.assertEqual(response_data["payload"]["start_promo"], "2020-06-21")
            self.assertEqual(response_data["payload"]["start"], "2020-07-01")
            self.assertEqual(response_data["payload"]["end"], "2020-07-31")
