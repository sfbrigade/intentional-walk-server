import json
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View, generic
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist

from .models import AppUser, DailyWalk, IntentionalWalk


# Function to validate the json payload to ensure required parameters exist
# for different api endpoints
def validate_request_json(json_data, required_fields=["name", "email", "zip", "age", "account_id"]):
    for required_field in required_fields:
        if required_field not in json_data:
            return {
                "valid": False,
                "json_response": {
                    "status": "error",
                    "message": f"Required input '{required_field}' missing in the request",
                },
            }

    return {"valid": True}


@method_decorator(csrf_exempt, name="dispatch")
class AppUserCreateView(View):
    model = AppUser
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        # Parse the body json
        json_data = json.loads(request.body)

        # Validate json. If any field is missing, send back an error
        json_status = validate_request_json(json_data, required_fields=["name", "email", "zip", "age", "account_id"])
        # If the json is not validated, return the response sent
        if not json_status["valid"]:
            return JsonResponse(json_status["json_response"])

        # Update if the object exists else create
        # EMAIL CANNOT BE UPDATED!
        try:
            appuser = AppUser.objects.get(account_id=json_data["account_id"])
            # If it is an email update
            if appuser.email != json_data["email"]:
                return JsonResponse({"status": "error", "message": "Email cannot be updated. Contact admin"})
            appuser.name = json_data["name"]
            appuser.zip = json_data["zip"]
            appuser.age = json_data["age"]
            appuser.save()
            return JsonResponse(
                {
                    "status": "success",
                    "message": "App User updated successfully",
                    "payload": {
                        "name": appuser.name,
                        "email": appuser.email,
                        "zip": appuser.zip,
                        "age": appuser.age,
                        "account_id": appuser.account_id,
                    },
                }
            )

        # This implies that it is a new user
        except ObjectDoesNotExist:
            obj = AppUser.objects.create(
                name=json_data["name"],
                email=json_data["email"],
                zip=json_data["zip"],
                age=json_data["age"],
                account_id=json_data["account_id"],
            )

            # To validate, retrieve the object back and send the details in the response
            try:
                appuser = AppUser.objects.get(email=json_data["email"], account_id=json_data["account_id"])
            except ObjectDoesNotExist:
                return JsonResponse(
                    {"status": "error", "message": "App User failed to save successfully. Please retry",}
                )

            return JsonResponse(
                {
                    "status": "success",
                    "message": "App User registered successfully",
                    "payload": {
                        "name": appuser.name,
                        "email": appuser.email,
                        "zip": appuser.zip,
                        "age": appuser.age,
                        "account_id": appuser.account_id,
                    },
                }
            )

    def http_method_not_allowed(self, request):
        return JsonResponse({"status": "error", "message": "Method not allowed!"})


@method_decorator(csrf_exempt, name="dispatch")
class DailyWalkCreateView(View):
    model = DailyWalk
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        json_data = json.loads(request.body)

        # Validate json. If any field is missing, send back an error
        json_status = validate_request_json(json_data, required_fields=["event_id", "account_id", "date", "steps"],)
        # If the json is not validated, return the response sent
        if not json_status["valid"]:
            return JsonResponse(json_status["json_response"])

        # Get the app user if the account exists
        try:
            appuser = AppUser.objects.get(account_id=json_data["account_id"])
        except ObjectDoesNotExist:
            return JsonResponse(
                {
                    "status": "error",
                    "message": f"User does not exist for account - {json_data['account_id']}. Please register first!",
                }
            )

        # Check if there is already an entry for this date.
        # If yes, ensure that "update": true is passed in the payload for an update
        # Otherwise, throw an error
        try:
            daily_walk = DailyWalk.objects.get(appuser=appuser, date=json_data["date"])
            if "update" in json_data and json_data["update"]:
                daily_walk.steps = json_data["steps"]
                daily_walk.event_id = json_data["event_id"]
                daily_walk.save()
                return JsonResponse(
                    {"status": "success", "message": f"Steps updated successfully for {json_data['date']}"}
                )
            else:
                return JsonResponse(
                    {
                        "status": "error",
                        "message": f"Steps already logged for {json_data['date']}. To update, please send 'update': True in input params",
                    }
                )
        except ObjectDoesNotExist:
            daily_walk = DailyWalk.objects.create(
                event_id=json_data["event_id"], date=json_data["date"], steps=json_data["steps"], appuser=appuser
            )

            return JsonResponse(
                {
                    "status": "success",
                    "message": "Dailywalk recorded successfully",
                    "payload": {
                        "event_id": daily_walk.event_id,
                        "account_id": appuser.account_id,
                        "date": daily_walk.date,
                        "steps": daily_walk.steps,
                    },
                }
            )

    def http_method_not_allowed(self, request):
        return JsonResponse({"status": "error", "message": "Method not allowed!"})


@method_decorator(csrf_exempt, name="dispatch")
class DailyWalkListView(View):
    model = DailyWalk
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        json_data = json.loads(request.body)

        # Validate json. If any field is missing, send back an error
        json_status = validate_request_json(json_data, required_fields=["account_id"])
        # If the json is not validated, return the response sent
        if not json_status["valid"]:
            return JsonResponse(json_status["json_response"])

        reverse_order = json_data["reverse_order"] if "reverse_order" in json_data else False
        num_walks = json_data["num_walks"] if "num_walks" in json_data else None

        try:
            appuser = AppUser.objects.get(account_id=json_data["account_id"])
        except ObjectDoesNotExist:
            return JsonResponse(
                {
                    "status": "error",
                    "message": f"User does not exist for account - {json_data['account_id']}. Please register first!",
                }
            )

        # Order based on the parameters
        if reverse_order:
            daily_walks = DailyWalk.objects.filter(appuser=appuser).order_by("date")[:num_walks]
        else:
            daily_walks = DailyWalk.objects.filter(appuser=appuser)[:num_walks]

        # Hacky serializer
        total_steps = 0
        daily_walk_list = []
        for daily_walk in daily_walks:
            daily_walk_list.append({"date": daily_walk.date, "steps": daily_walk.steps})
            total_steps += daily_walk.steps

        payload = {"daily_walks": daily_walk_list, "total_steps": total_steps, "status": "success"}

        return JsonResponse(payload)

    def http_method_not_allowed(self, request):
        return JsonResponse({"status": "error", "message": "Method not allowed!"})


@method_decorator(csrf_exempt, name="dispatch")
class IntentionalWalkView(View):
    model = IntentionalWalk
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        json_data = json.loads(request.body)

        # Validate json. If any field is missing, send back an error
        json_status = validate_request_json(
            json_data, required_fields=["event_id", "email", "account_id", "start", "end", "steps",],
        )
        # If the json is not validated, return the response sent
        if not json_status["valid"]:
            return JsonResponse(json_status["json_response"])

        try:
            appuser = AppUser.objects.get(email=json_data["email"], account_id=json_data["account_id"])
        except ObjectDoesNotExist:
            return JsonResponse({"status": "error", "message": "User/device not registered"})

        _ = IntentionalWalk.objects.create(
            start=json_data["start"], end=json_data["end"], steps=json_data["steps"], appuser=appuser,
        )

        return JsonResponse({"status": "success", "message": "Intentional Walk recorded successfully"})

    def http_method_not_allowed(self, request):
        return JsonResponse({"status": "error", "message": "Method not allowed!"})


@method_decorator(csrf_exempt, name="dispatch")
class IntentionalWalkListView(View):
    model = IntentionalWalk
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        json_data = json.loads(request.body)

        # Validate json. If any field is missing, send back an error
        json_status = validate_request_json(json_data, required_fields=["email", "account_id"])
        # If the json is not validated, return the response sent
        if not json_status["valid"]:
            return JsonResponse(json_status["json_response"])

        reverse_order = json_data["reverse_order"] if "reverse_order" in json_data else False
        num_walks = json_data["num_walks"] if "num_walks" in json_data else None

        try:
            appuser = AppUser.objects.get(email=json_data["email"], account_id=json_data["account_id"])
        except ObjectDoesNotExist:
            return JsonResponse({"status": "error", "message": "User/device not registered"})

        # Order based on the parameters
        if reverse_order:
            intentional_walks = IntentionalWalk.objects.filter(appuser=appuser).order_by("start")[:num_walks]
        else:
            intentional_walks = IntentionalWalk.objects.filter(appuser=appuser)[:num_walks]

        # Hacky serializer
        total_steps = 0
        intentional_walk_list = []
        for intentional_walk in intentional_walks:
            intentional_walk_list.append(
                {"start": intentional_walk.start, "end": intentional_walk.end, "steps": intentional_walk.steps,}
            )
            total_steps += intentional_walk.steps

        payload = {
            "intentional_walks": intentional_walk_list,
            "total_steps": total_steps,
        }

        return JsonResponse(payload)

    def http_method_not_allowed(self, request):
        return JsonResponse({"status": "error", "message": "Method not allowed!"})
