import json
import logging
from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from home.models import WeeklyGoal, Device
from home.utils.dates import get_start_of_week, DATE_FORMAT


from .utils import validate_request_json

logger = logging.getLogger(__name__)


# Exempt from csrf validation
@method_decorator(csrf_exempt, name="dispatch")
class WeeklyGoalCreateView(View):
    """View to create or update a weeklygoal for an account"""

    model = WeeklyGoal
    http_method_names = ["post"]

    def post(self, request):
        json_data = json.loads(request.body)

        # Validate json. If any field is missing, send back the response message
        json_status = validate_request_json(
            json_data,
            required_fields=["account_id", "weekly_goal"],
        )
        if "status" in json_status and json_status["status"] == "error":
            return JsonResponse(json_status)

        # Validate weekly_goal json fields
        json_status = validate_request_json(
            json_data["weekly_goal"],
            required_fields=["start_of_week", "steps", "days"],
        )

        if "status" in json_status and json_status["status"] == "error":
            return JsonResponse(json_status)

        # Get the device
        try:
            device = Device.objects.get(device_id=json_data["account_id"])
            account = device.account
        except ObjectDoesNotExist:
            return JsonResponse(
                {
                    "status": "error",
                    "message": (
                        "Unregistered device - "
                        f"{json_data['account_id']}."
                        " Please register first!"
                    ),
                }
            )

        # Json response template
        json_response = {
            "status": "success",
            "message": "WeeklyGoal saved successfully",
            "payload": {
                "account_id": account.id,
                "weekly_goal": {},
            },
        }

        weekly_goal_update = json_data["weekly_goal"]

        start_of_week = weekly_goal_update["start_of_week"]
        start_of_week_update = get_start_of_week(
            datetime.strptime(start_of_week, DATE_FORMAT).date()
        )
        steps_update = weekly_goal_update["steps"]
        days_update = weekly_goal_update["days"]

        # Check if there's already a goal for the week. If there is,
        # update the entry.
        try:
            weekly_goal = WeeklyGoal.objects.get(
                account=account,
                start_of_week=start_of_week_update,
            )
            weekly_goal.steps = steps_update
            weekly_goal.days = days_update
            weekly_goal.save()
        except ObjectDoesNotExist:
            # Creation if object is missing
            weekly_goal = WeeklyGoal.objects.create(
                start_of_week=start_of_week_update,
                steps=steps_update,
                days=days_update,
                account=account,
            )

        # Update the json object
        json_response["payload"]["weekly_goal"] = {
            "start_of_week": weekly_goal.start_of_week,
            "steps": weekly_goal.steps,
            "days": weekly_goal.days,
        }

        return JsonResponse(json_response)

    def http_method_not_allowed(self, request):
        return JsonResponse(
            {"status": "error", "message": "Method not allowed!"}
        )


@method_decorator(csrf_exempt, name="dispatch")
class WeeklyGoalsListView(View):
    """View to retrieve Weekly Goals"""

    model = WeeklyGoal
    http_method_name = ["post"]

    def post(self, request):
        json_data = json.loads(request.body)

        # Validate json. If any field is missing, send back the response message
        json_status = validate_request_json(
            json_data, required_fields=["account_id"]
        )

        if "status" in json_status and json_status["status"] == "error":
            return JsonResponse(json_status)

        # Get the account
        try:
            device = Device.objects.get(device_id=json_data["account_id"])
            account = device.account
        except ObjectDoesNotExist:
            return JsonResponse(
                {
                    "status": "error",
                    "message": (
                        "Unregistered account - "
                        f"{json_data['account_id']}."
                        " Please register first!"
                    ),
                }
            )

        # Json response template
        json_response = {
            "status": "success",
            "message": "Weekly goals accessed successfully",
            "payload": {},
        }

        # Get weekly goals tied to this account
        weekly_goals = list(
            WeeklyGoal.objects.filter(account=account).values()
        )
        """ for goal in weekly_goals:
            goal = model_to_dict(goal) """
        for goal in weekly_goals:
            goal["start_of_week"] = goal["start_of_week"].strftime(DATE_FORMAT)

        json_response["payload"] = weekly_goals

        return JsonResponse(json_response)

    def http_method_not_allowed(self, request):
        return JsonResponse(
            {"status": "error", "message": "Method not allowed!"}
        )
