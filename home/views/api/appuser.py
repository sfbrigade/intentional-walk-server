import json
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist

from home.models import Account, Device
from home.models.account import SAN_FRANCISCO_ZIP_CODES, GenderLabels, IsLatinoLabels, RaceLabels, SexualOrientationLabels
from .utils import validate_request_json


# Determines whether Account is tester account, based on name prefix
def is_tester(name_field: str) -> bool:
    possible_prefixes = ["tester-", "tester ", "tester_"]
    return any([name_field.lower().startswith(prefix) for prefix in possible_prefixes])

# Validates Account input data. Raises AssertionError if field is invalid.
# Does not check for required fields since that is done by validate_request_json
def validate_account_input(data: dict):
    """
    Validation of account data input:
        * name:                 not empty
        * zip:                  length between 5 and 10
        * age:                  between 1 and 200
        * is_latino:            value must be in IsLatinoLabels
        * race:                 values must be in RaceLabels
        * race_other:           must (only) be specified when race includes 'OT'
        * gender:               value must be in GenderLabels
        * gender_other:         must (only) be specified when gender is 'OT'
        * sexual_orien:         value must be in SexualOrientationLabels
        * sexual_orien_other:   must (only) be specified when sexual_orien is 'OT'

    """
    if data.get("name") is not None: # Required field but existence checked in validate_request_json
        assert len(data["name"]) > 0, "Invalid name"
    if data.get("zip") is not None: # Required field but existence checked in validate_request_json
        assert len(data["zip"]) >= 5 and len(data["zip"]) <= 10, "Invalid zip code"
    if data.get("age") is not None: # Required field but existence checked in validate_request_json
        assert data["age"] > 1 and data["age"] < 200, "Invalid age"
    if data.get("is_latino") is not None:
        is_latino = data["is_latino"]
        assert is_latino in IsLatinoLabels.__members__, \
            f"Invalid is latino or hispanic selection '{is_latino}'"
    if data.get("race") is not None:
        for item in data["race"]:
            assert item in RaceLabels.__members__, f"Invalid race selection '{item}'"
        if "OT" in data["race"]:
            assert len(data.get("race_other", "")) > 0, "Must specify 'other' race"
        else:
            assert data.get("race_other") is None, "'race_other' should not be specified without race 'OT'"
    elif data.get("race_other") is not None:
        assert False, "'race_other' should not be specified without 'race'"
    if data.get("gender") is not None:
        gender = data["gender"]
        assert gender in GenderLabels.__members__, \
            f"Invalid gender selection '{gender}'"
        if data["gender"] == "OT":
            assert len(data.get("gender_other", "")) > 0, "Must specify 'other' gender"
        else:
            assert data.get("gender_other") is None, "'gender_other' should not be specified without 'OT'"
    elif data.get("gender_other") is not None:
        assert False, "'gender_other' should not be specified without 'gender'"
    if data.get("sexual_orien") is not None:
        sexual_orientation = data["sexual_orien"]
        assert sexual_orientation in SexualOrientationLabels.__members__, \
            f"Invalid sexual orientation selection '{sexual_orientation}'"
        if data["sexual_orien"] == "OT":
            assert len(data.get("sexual_orien_other", "")) > 0, "Must specify 'other' sexual orientation"
        else:
            assert data.get("sexual_orien_other") is None, "'sexual_orien_other' should not be specified without 'OT'"
    elif data.get("sexual_orien_other") is not None:
        assert False, "'sexual_orien_other' should not be specified without 'gender'"

def update_account(acct: Account, data: dict):
    # Data fields vary based on registration screen

    # Screen 1: Name, Email, Zip, Age.
    # Not possible to update email
    if data.get("name") is not None:
        acct.name = data["name"]
        acct.is_tester = is_tester(data["name"])

    if data.get("zip") is not None:
        acct.zip = data["zip"]
        acct.is_sf_resident = data["zip"] in SAN_FRANCISCO_ZIP_CODES

    if data.get("age") is not None:
        acct.age = data["age"]

    # Screen 2. Latino/Hispanic Origin
    if data.get("is_latino") is not None:
        acct.is_latino = data.get("is_latino")

    # Screen 3. Race
    if data.get("race") is not None:
        acct.race = data.get("race", [])
        acct.race_other = data.get("race_other")

    # Screen 4. Gender Identity
    if data.get("gender") is not None:
        acct.gender = data.get("gender")
        acct.gender_other = data.get("gender_other")

    # Screen 5. Sexual Orientation
    if data.get("sexual_orien") is not None:
        acct.sexual_orien = data.get("sexual_orien")
        acct.sexual_orien_other = data.get("sexual_orien_other")
    acct.save()

# Except from csrf validation
@method_decorator(csrf_exempt, name="dispatch")
class AppUserCreateView(View):
    """API interface to register a device and a user account on app install.
    If already present, the same endpoint will update user details except email.
    """

    http_method_names = ["post", "put"]

    def put(self, request, *args, **kwargs):
        json_data = json.loads(request.body)

        # Validate json. If account_id is missing, send back the response message
        json_status = validate_request_json(json_data, required_fields=["account_id"])
        if "status" in json_status and json_status["status"] == "error":
            return JsonResponse(json_status)

        # Update user attributes.
        device = Device.objects.get(device_id=json_data["account_id"])
        account = Account.objects.get(email=device.account.email)
        update_account(account, json_data)
        message = "Account updated successfully"

        return JsonResponse(
            {
                "status": "success",
                "message": message,
            }
        )


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

        # For a participating device
        try:
            # NOTE: Account id here maps to a device id. Perhaps the API definition could
            # be changed in the future
            # Get the registered device if it exists
            device = Device.objects.get(device_id=json_data["account_id"])
            # If it is an email update fail and return
            if device.account.email != json_data["email"]:
                return JsonResponse({"status": "error", "message": "Email cannot be updated. Contact admin"})

            # Otherwise, update the account's other details
            account = Account.objects.get(email=json_data["email"])
            update_account(account, json_data)
            message = "Device & account updated successfully"

        # This implies that it is a new device
        except ObjectDoesNotExist:
            # Check if the user account exists. If not, create it
            try:
                account = Account.objects.get(email=json_data["email"])
                update_account(account, json_data)
                message = "Account updated successfully"
                account_updated = True
            except ObjectDoesNotExist:
                # Partially create account first, with required fields
                account = Account.objects.create(
                    email=json_data["email"],
                    name=json_data["name"],
                    zip=json_data["zip"],
                    age=json_data["age"],
                )
                account_updated = False


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
                    "account_id": device.device_id,
                    "name": account.name,
                    "email": account.email,
                    "zip": account.zip,
                    "age": account.age,
                    "is_latino": account.is_latino,
                    "race": list(account.race),
                    "race_other": account.race_other,
                    "gender": account.gender,
                    "gender_other": account.gender_other,
                    "sexual_orien": account.sexual_orien,
                    "sexual_orien_other": account.sexual_orien_other,
                },
            }
        )

    def http_method_not_allowed(self, request):
        return JsonResponse({"status": "error", "message": "Method not allowed!"})
