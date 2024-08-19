from django.contrib.auth.models import AnonymousUser, User
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.views import View

from home.tests.integration.apiv1.views.api.utils import Login
from home.views.api.utils import require_authn


class TestAuthn(TestCase):
    def setUp(self):
        # Create a test view that uses the require_authn decorator
        class TestView(View):
            @require_authn
            def get(self, request):
                return HttpResponse("Hello, World!")

        self.view = TestView.as_view()
        self.factory = RequestFactory()

    def test_authenticated(self):
        Login()
        self.user = User.objects.get(username=Login.username)

        # Create a request and authenticate the user
        request = self.factory.get("/")
        request.user = self.user

        response = self.view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Hello, World!")

    def test_unauthenticated(self):
        # Create a request and don't authenticate the user
        request = self.factory.get("/")
        request.user = AnonymousUser()

        response = self.view(request)
        self.assertEqual(response.status_code, 401)
