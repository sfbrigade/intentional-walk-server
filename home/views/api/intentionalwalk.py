import json
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View, generic
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist

from home.models import Account, Device, IntentionalWalk
from .utils import validate_request_json


@method_decorator(csrf_exempt, name="dispatch")
class IntentionalWalkView(View):
    """View to create Intentional Walks
    """

    model = IntentionalWalk
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        json_data = json.loads(request.body)

        # Validate json. If any field is missing, send back the response message
        json_status = validate_request_json(json_data, required_fields=["account_id", "intentional_walks"],)
        if "status" in json_status and json_status["status"] == "error":
            return JsonResponse(json_status)

        # Get the device if already registered
        try:
            device = Device.objects.get(device_id=json_data["account_id"])
        except ObjectDoesNotExist:
            return JsonResponse(
                {
                    "status": "error",
                    "message": f"Unregistered device - {json_data['account_id']}. Please register first!",
                }
            )

        json_response = {
            "status": "success",
            "message": "Intentional Walks recorded successfully",
            "payload": {"account_id": device.device_id, "intentional_walks": []},
        }

        # Loop through all the intentional walks
        for intentional_walk_data in json_data["intentional_walks"]:

            json_status = validate_request_json(
                intentional_walk_data, required_fields=["event_id", "start", "end", "steps", "pause_time", "distance"],
            )
            if "status" in json_status and json_status["status"] == "error":
                return JsonResponse(json_status)

            try:
                intentional_walk = IntentionalWalk.objects.create(
                    event_id=intentional_walk_data["event_id"],
                    start=intentional_walk_data["start"],
                    end=intentional_walk_data["end"],
                    steps=intentional_walk_data["steps"],
                    distance=intentional_walk_data["distance"],
                    pause_time=intentional_walk_data["pause_time"],
                    device=device,
                )
                json_response["payload"]["intentional_walks"].append(
                    {
                        "event_id": intentional_walk.event_id,
                        "start": intentional_walk.start,
                        "end": intentional_walk.end,
                        "steps": intentional_walk.steps,
                        "distance": intentional_walk.distance,
                        "pause_time": intentional_walk.pause_time,
                    }
                )
            except:
                # IntentionalWalk records are immutable- so ignore any errors
                # that might occur if the record already exists, etc...
                pass

        return JsonResponse(json_response)

    def http_method_not_allowed(self, request):
        return JsonResponse({"status": "error", "message": "Method not allowed!"})


@method_decorator(csrf_exempt, name="dispatch")
class IntentionalWalkListView(View):
    """View to retrieve Intentional Walks
    """

    model = IntentionalWalk
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        json_data = json.loads(request.body)

        # Validate json. If any field is missing, send back the response message
        json_status = validate_request_json(json_data, required_fields=["account_id"])
        if "status" in json_status and json_status["status"] == "error":
            return JsonResponse(json_status)

        # Get the device if already registered
        try:
            device = Device.objects.get(device_id=json_data["account_id"])
        except ObjectDoesNotExist:
            return JsonResponse(
                {
                    "status": "error",
                    "message": f"Unregistered device - {json_data['account_id']}. Please register first!",
                }
            )

        # Get walks from all the accounts tied to the email
        intentional_walks = IntentionalWalk.objects.filter(account__email=device.account.email)

        # Hacky serializer
        total_steps = 0
        total_walk_time = 0
        total_pause_time = 0
        total_distance = 0
        intentional_walk_list = []
        for intentional_walk in intentional_walks:
            intentional_walk_list.append(
                {
                    "start": intentional_walk.start,
                    "end": intentional_walk.end,
                    "steps": intentional_walk.steps,
                    "distance": intentional_walk.distance,
                    "walk_time": intentional_walk.walk_time,
                    "pause_time": intentional_walk.pause_time,
                }
            )
            total_steps += intentional_walk.steps
            total_walk_time += intentional_walk.walk_time
            total_distance += intentional_walk.distance
            total_pause_time += intentional_walk.pause_time
        intentional_walk_list = sorted(intentional_walk_list, key=lambda x: x["start"], reverse=True)
        payload = {
            "intentional_walks": intentional_walk_list,
            "total_steps": total_steps,
            "total_walk_time": total_walk_time,
            "total_pause_time": total_pause_time,
            "total_distance": total_distance,
            "status": "success",
        }

        return JsonResponse(payload)

    def http_method_not_allowed(self, request):
        return JsonResponse({"status": "error", "message": "Method not allowed!"})
