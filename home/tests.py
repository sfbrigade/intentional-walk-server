import json
from django.test import Client, TestCase
from home.models import AppUser

class ApiTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_create_appuser(self):
        # register a new user
        response = self.client.post('/api/appuser/create', {
        	"name": "Abhay Kashyap",
        	"email": "abhay@blah.com",
        	"zip": 72185,
        	"age": 99,
        	"device_id": 12345,
        }, 'application/json')
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertDictEqual(response_data, {"status": "success", "message": "App User registered successfully"})
        self.assertEqual(AppUser.objects.count(), 1)

        # re-register on a new device, update user record
        response = self.client.post('/api/appuser/create', {
        	"name": "Abhay Kashyap",
        	"email": "abhay@blah.com",
        	"zip": 72185,
        	"age": 99,
        	"device_id": 54321,
        }, 'application/json')
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertDictEqual(response_data, {"status": "success", "message": "App User updated successfully"})
        self.assertEqual(AppUser.objects.count(), 1)
