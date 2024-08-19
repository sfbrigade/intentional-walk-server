from django.test import Client, TestCase

from home.models import Device


class ApiTestCase(TestCase):
    def setUp(self):
        # Test client
        self.client = Client()
        # Constants
        self.device_id = "12345"

        # Content type
        self.content_type = "application/json"

        # Register the user
        response = self.client.post(
            path="/api/v2/appuser",
            data={
                "name": "John Doe",
                "email": "john@blah.com",
                "zip": "94102",
                "age": 99,
                "account_id": self.device_id,
            },
            content_type=self.content_type,
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 201)

        # Url for device update
        self.url = "/api/v2/device"

        self.request_params = {
            "device_model": "iPhone16,1",
            "manufacturer": "Apple",
            "os_name": "iOS",
            "os_version": "17.5",
        }

    # Test patching a User's device
    def test_update_device_patch(self):
        for field, value in self.request_params.items():
            # Update value
            request_params = {
                "device_id": self.device_id,
                field: value,
            }

            # Register the user
            response = self.client.patch(
                path=f"{self.url}/{self.device_id}",
                data=request_params,
                content_type=self.content_type,
            )

            # Check for a successful response by the server
            self.assertEqual(response.status_code, 204)

            # Check for a successful update in the database
            device_obj = Device.objects.get(device_id=self.device_id)
            self.assertEqual(
                getattr(device_obj, field),
                value,
                msg=f"field: {field} - Expected: {value} \
                        Got: {getattr(device_obj, field)}",
            )

    # Test updating a User's device using put method
    def test_update_device_put(self):
        # Update value
        request_params = {
            **self.request_params,
            "device_id": self.device_id,
        }
        # Update the user's device for the first time
        response = self.client.put(
            path=f"{self.url}/{self.device_id}",
            data=request_params,
            content_type=self.content_type,
        )

        # Check for a successful response by the server
        self.assertEqual(response.status_code, 204)

        # Check for a successful update in the database
        device_obj = Device.objects.get(device_id=self.device_id)
        for field, value in self.request_params.items():
            self.assertEqual(
                getattr(device_obj, field),
                value,
                msg=f"field: {field} - Expected: {value} \
                        Got: {getattr(device_obj, field)}",
            )

        # Change OS version
        request_params["os_version"] = "17.6.1"

        # Update the user's device os_version
        response = self.client.put(
            path=f"{self.url}/{self.device_id}",
            data=request_params,
            content_type=self.content_type,
        )

        # Check for a successful response by the server
        self.assertEqual(response.status_code, 204)

        # Check for a successful update in the database
        device_obj = Device.objects.get(device_id=self.device_id)
        self.assertEqual(getattr(device_obj, "os_version"), "17.6.1")
        for field, value in request_params.items():
            self.assertEqual(
                getattr(device_obj, field),
                value,
                msg=f"field: {field} - Expected: {value} \
                        Got: {getattr(device_obj, field)}",
            )

    # Test updating User's device without providing device_id
    def test_update_device_missing_account_id(self):
        # Required request parameters
        request_params = {
            **self.request_params,
            "device_id": self.device_id,
        }
        # Update the user's device for the first time
        response = self.client.put(
            path=f"{self.url}/{self.device_id}",
            data=request_params,
            content_type=self.content_type,
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 204)

        # Test with device_id missing from path parameter
        # Patch method
        response = self.client.patch(
            path=f"{self.url}/",
            data=request_params,
            content_type=self.content_type,
        )
        # Check for a 404 response by the server
        self.assertEqual(response.status_code, 404)
        # Parse the response
        response_data = response.content
        fail_message = f"Server response - {response_data}"
        self.assertIn(b"Not Found", response_data, msg=fail_message)

        # Test with device_id missing from path parameter
        # Put method
        response = self.client.put(
            path=f"{self.url}/",
            data=request_params,
            content_type=self.content_type,
        )
        # Check for a 404 response by the server
        self.assertEqual(response.status_code, 404)
        # Parse the response
        response_data = response.content
        fail_message = f"Server response - {response_data}"
        self.assertIn(b"Not Found", response_data, msg=fail_message)

        # Remove the device_id field
        del request_params["device_id"]

        # Test with device_id missing from payload
        # Patch method
        response = self.client.patch(
            path=f"{self.url}/{self.device_id}",
            data=request_params,
            content_type=self.content_type,
        )
        # Check for a 422 response by the server
        self.assertEqual(response.status_code, 422)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(
            response_data["detail"][0]["type"], "missing", msg=fail_message
        )
        self.assertIn(
            "device_id", response_data["detail"][0]["loc"], msg=fail_message
        )
        self.assertEqual(
            response_data["detail"][0]["msg"],
            "Field required",
            msg=fail_message,
        )

        # Test with device_id missing from payload
        # Put method
        response = self.client.put(
            path=f"{self.url}/{self.device_id}",
            data=request_params,
            content_type=self.content_type,
        )
        # Check for a 422 response by the server
        self.assertEqual(response.status_code, 422)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"
        self.assertEqual(
            response_data["detail"][0]["type"], "missing", msg=fail_message
        )
        self.assertIn(
            "device_id", response_data["detail"][0]["loc"], msg=fail_message
        )
        self.assertEqual(
            response_data["detail"][0]["msg"],
            "Field required",
            msg=fail_message,
        )

    def test_update_device_invalid_device_id(self):
        # Required request parameters
        request_params = {
            **self.request_params,
            "device_id": "fakeID",
        }

        # Update nonexistent user using patch method
        response = self.client.patch(
            path=f"{self.url}/fakeID",
            data=request_params,
            content_type=self.content_type,
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 404)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"

        self.assertEqual(
            response_data["detail"],
            "Unregistered device - device_id: fakeID. Please register first!",
            msg=fail_message,
        )

        # Update nonexistent user using put method
        response = self.client.put(
            path=f"{self.url}/fakeID",
            data=request_params,
            content_type=self.content_type,
        )
        # Check for a successful response by the server
        self.assertEqual(response.status_code, 404)
        # Parse the response
        response_data = response.json()
        fail_message = f"Server response - {response_data}"

        self.assertEqual(
            response_data["detail"],
            "Unregistered device - device_id: fakeID. Please register first!",
            msg=fail_message,
        )

    # Test invalid methods
    def test_device_invalid_methods(self):
        # Required fields for device
        request_params = {**self.request_params, "device_id": self.device_id}

        # Test get method
        response = self.client.get(
            path=f"{self.url}/{self.device_id}",
            data=request_params,
            content_type=self.content_type,
        )
        # Check for a 405 response by the server
        self.assertEqual(response.status_code, 405)
        # Parse the response
        response_data = response.content
        fail_message = f"Server response - {response_data}"
        self.assertEqual(
            response_data, b"Method not allowed", msg=fail_message
        )

        # Test get method
        response = self.client.get(
            path=self.url, data=request_params, content_type=self.content_type
        )
        # Check for a 404 response by the server
        self.assertEqual(response.status_code, 404)
        # Parse the response
        response_data = response.content
        fail_message = f"Server response - {response_data}"
        self.assertIn(b"Not Found", response_data, msg=fail_message)
