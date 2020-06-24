import json
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist

from home.models import Account, Device
from .utils import validate_request_json

# Except from csrf validation
@method_decorator(csrf_exempt, name="dispatch")
class AppUserCreateView(View):
    """API interface to register a device and a user account on app install.
    If already present, the same endpoint will update user details except email.
    """

    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        # Parse the body json
        json_data = json.loads(request.body)

        # Validate json. If any field is missing, send back the response message
        json_status = validate_request_json(json_data, required_fields=["name", "email", "zip", "age", "account_id"])
        if "status" in json_status and json_status["status"] == "error":
            return JsonResponse(json_status)

        # Update user attributes if the object exists, else create.
        # EMAIL CANNOT BE UPDATED!
        # NOTE: Ideally, email ids should be validated by actually sending emails
        # Currently, accidental/intentional use of the same email id will share data
        # across devices. In such an instance, a new account with the correct email
        # must be created to separate data. Otherwise, attribution will be to the account
        # email created first.
        try:
            # NOTE: Account id here maps to a device id. Perhaps the API definition could
            # be changed in the future
            # Get the registered device if it exists
            device = Device.objects.get(device_id=json_data["account_id"])

            # If it is an email update fail and return
            if device.account.email != json_data["email"]:
                return JsonResponse({"status": "error", "message": "Email cannot be updated. Contact admin"})

            # Otherwise, update the account's other details
            device.account.name = json_data["name"]
            device.account.zip = json_data["zip"]
            device.account.age = json_data["age"]
            device.account.save()

            message = "Device & account updated successfully"

        # This implies that it is a new device
        except ObjectDoesNotExist:
            # Check if the user account exists. If not, create it
            account_updated = False
            try:
                account = Account.objects.get(email=json_data["email"])
                account.name = json_data["name"]
                account.zip = json_data["zip"]
                account.age = json_data["age"]
                account.save()
                account_updated = True
            except ObjectDoesNotExist:
                account = Account.objects.create(
                    email=json_data["email"], name=json_data["name"], age=json_data["age"], zip=json_data["zip"]
                )

            # Create a new device object and link it to the account
            device = Device.objects.create(device_id=json_data["account_id"], account=account)
            updated_str = "updated" if account_updated else "registered"
            message = f"Device registered & account {updated_str} successfully"

        # To validate, retrieve the object back and send the details in the response
        try:
            device = Device.objects.get(device_id=json_data["account_id"])
        except ObjectDoesNotExist:
            return JsonResponse({"status": "error", "message": "App User failed to save successfully. Please retry",})

        return JsonResponse(
            {
                "status": "success",
                "message": message,
                "payload": {
                    "name": device.account.name,
                    "email": device.account.email,
                    "zip": device.account.zip,
                    "age": device.account.age,
                    "account_id": device.device_id,
                },
            }
        )

    def http_method_not_allowed(self, request):
        return JsonResponse({"status": "error", "message": "Method not allowed!"})
