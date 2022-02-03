import json
import logging

from datetime import date
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View, generic
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist

from home.models import Contest, Device, Account, DailyWalk
from .utils import validate_request_json


logger = logging.getLogger(__name__)

# Except from csrf validation
@method_decorator(csrf_exempt, name="dispatch")
class DailyWalkCreateView(View):
    """View to create or update a list of dailywalks from a registered device
    """

    model = DailyWalk
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        json_data = json.loads(request.body)

        # Validate json. If any field is missing, send back the response message
        json_status = validate_request_json(json_data, required_fields=["account_id", "daily_walks"],)
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

        # Json response template
        json_response = {
            "status": "success",
            "message": f"Dailywalks recorded successfully",
            "payload": {"account_id": device.device_id, "daily_walks": [],},
        }

        active_contests = set()

        for daily_walk_data in json_data["daily_walks"]:
            # Validate data
            json_status = validate_request_json(daily_walk_data, required_fields=["date", "steps", "distance"],)
            if "status" in json_status and json_status["status"] == "error":
                return JsonResponse(json_status)

            walk_date = daily_walk_data["date"]

            # Register contest for account if walk_date falls between contest start and contest end
            # (Can be async)
            contest = Contest.active(for_date=date.fromisoformat(walk_date), strict=True)
            if contest is not None:
                active_contests.add(contest)

            # Check if there is already an entry for this date. If there is, update the entry
            # NOTE: By definition, there should be one and only one entry for a given email and date
            # NOTE: This is a potential vulnerability. Since there is no email authentication at the moment,
            # anyone can simply spoof an email id with a new device and overwrite daily walk data for the target email
            # This is also a result of no session auth (can easily hit the api directly)
            try:
                # Updation
                daily_walk = DailyWalk.objects.get(account__email=device.account.email, date=walk_date)
                daily_walk.steps = daily_walk_data["steps"]
                daily_walk.distance = daily_walk_data["distance"]
                daily_walk.device_id = json_data["account_id"]
                daily_walk.save()
            except ObjectDoesNotExist:
                # Creation if object is missing
                daily_walk = DailyWalk.objects.create(
                    date=walk_date,
                    steps=daily_walk_data["steps"],
                    distance=daily_walk_data["distance"],
                    device=device,
                )

            # Update the json object
            json_response["payload"]["daily_walks"].append(
                {"date": daily_walk.date, "steps": daily_walk.steps, "distance": daily_walk.distance}
            )

        # Associate contest with user (account)
        for contest in active_contests:
            try:
                acct = device.account
                acct.contests.add(contest)
            except:
                logger.error(f"Could not associate contest {contest} with account {acct}!", exc_info=True)

        return JsonResponse(json_response)

    def http_method_not_allowed(self, request):
        return JsonResponse({"status": "error", "message": "Method not allowed!"})


@method_decorator(csrf_exempt, name="dispatch")
class DailyWalkListView(View):
    """View to retrieve Daily Walks
    """

    model = DailyWalk
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
            # appuser = AppUser.objects.get(account_id=json_data["account_id"])
        except ObjectDoesNotExist:
            return JsonResponse(
                {
                    "status": "error",
                    "message": f"Unregistered device - {json_data['account_id']}. Please register first!",
                }
            )

        # Get walks from tied to this account
        # NOTE: This is very hacky and cannot distinguish between legit and fake users
        # Someone can simply install the app on a new device and use a known email id
        # and have the metrics simply aggregated.
        # For the simple use case, this is likely not an issue and would need to be
        # handled manually if needed
        daily_walks = DailyWalk.objects.filter(account__email=device.account.email)

        # Hacky serializer
        total_steps = 0
        total_distance = 0
        daily_walk_list = []
        for daily_walk in daily_walks:
            daily_walk_list.append(
                {"date": daily_walk.date, "steps": daily_walk.steps, "distance": daily_walk.distance}
            )
            total_steps += daily_walk.steps
            total_distance += daily_walk.distance

        # Sort the list based on the date
        daily_walk_list = sorted(daily_walk_list, key=lambda x: x["date"], reverse=True)
        # Create the payload with meta information and send it back
        payload = {
            "daily_walks": daily_walk_list,
            "total_steps": total_steps,
            "total_distance": total_distance,
            "status": "success",
        }
        return JsonResponse(payload)

    def http_method_not_allowed(self, request):
        return JsonResponse({"status": "error", "message": "Method not allowed!"})
