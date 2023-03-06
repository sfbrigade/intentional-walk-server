# from datetime import date, timedelta
# from typing import Optional
import json


from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.db.models.functions import RowNumber, Rank
from django.db.models.expressions import Window


from django.db.models import Count, F, Sum
from django.core.exceptions import ObjectDoesNotExist


from home.models import (
    # Account,
    Contest,
    # DailyWalk,
    # IntentionalWalk,
    Device,
    Leaderboard,
)

# from home.utils import localize
from .utils import validate_request_json

    #Dispatch?
@method_decorator(csrf_exempt, name="dispatch")
class LeaderboardListView(View):
    """View to retrieve leaderboard"""

    # model = DailyWalk
    http_method_names = ["get"]

   # def get(self, request, account_id, contest_id, *args, **kwargs):
    def get(self, request, *args, **kwargs):

        contest_id = request.GET.get("contest_id")
        account_id = request.GET.get("account_id")
        print("a", account_id)
        print("c", contest_id)
        print("r", request)

        # Parse params
        if contest_id is None:
            return HttpResponse("No current contest, check back during the next contest period!")


        current_contest = Contest.objects.filter(contest_id=contest_id)
        print("curr", current_contest)
        ## http://localhost:8000/api/leaderboard/get?contest_id=24dcb327-7ce4-4c6d-b33d-33a2606d30ec?account_id=691d690b-da13-4864-b5ff-4d1535a6528d
        # Validate request. If any field is missing, send back the response message
        # Get the device if already registered
        try:
            device = Device.objects.get(device_id=account_id)
        except ObjectDoesNotExist:
            return JsonResponse(
                {
                    "status": "error",
                    "message": (
                        "Unregistered device - "
                        "Please register first!"  
                        "account:" f"{account_id}"
                    ),
                }
            )
        # Json response template
        json_response = {
            "status": "success",
            "message": "Leaderboard accessed successfully",
            "payload": {
                "account_id": device.device_id,
                "leaderboard": [],
            },
        }

        leaderboard_list = []
        leaderboard_length = 10
        leaderboard = ( Leaderboard.objects.filter(contest=contest_id)
            .values("device_id",  "steps")
            .annotate(rank=Window(
            expression=Rank(),
            order_by=F('steps').desc()))
        )

        leaderboard_list = [user for user in leaderboard]  

        for count, user in enumerate(leaderboard_list):
            print("if", user["id"], json_data["account_id"])
            if (
                user["device_id"] == account_id
                and user["rank"] > leaderboard_length
            ):
                # current_user_range.append(leaderboard_list[count-1])
                # current_user_range.append(leaderboard_list[count])
                # current_user_range.append(leaderboard_list[count+1])
                current_user = user

        # cut list to 10 items, add current user
        leaderboard_list = leaderboard_list[:leaderboard_length]
        #leaderboard_list.append(current_user)
        # leaderboard_list.extend(current_user_range)
        json_response["payload"]["leaderboard"] = leaderboard_list

        if current_contest is None:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "There are no contests",
                }
            )
        return JsonResponse(json_response)
