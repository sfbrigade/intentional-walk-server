from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.db.models.functions import Rank
from django.db.models.expressions import Window
from django.db.models import F
from django.core.exceptions import ObjectDoesNotExist

from home.models import (
    Contest,
    Device,
    Leaderboard,
)


@method_decorator(csrf_exempt, name="dispatch")
# Dispatch?
class LeaderboardListView(View):
    """View to retrieve leaderboard"""

    # model = Leaderboard
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):

        contest_id = request.GET.get("contest_id")
        account_id = request.GET.get("account_id")

        # Parse params
        if contest_id is None:
            return HttpResponse(
                "No current contest, check back during the next contest period!"
            )

        current_contest = Contest.objects.filter(contest_id=contest_id)
        # http://localhost:8000/api/leaderboard/
        # get?contest_id=<contest>?account_id=<account_id>

        # Validate request. If any field is missing,
        #  send back the response message
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
                        "account:"
                        f"{account_id}"
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
        leaderboard = (
            Leaderboard.objects.filter(contest=contest_id)
            .values("device_id", "steps")
            .annotate(
                rank=Window(expression=Rank(), order_by=F("steps").desc())
            )
        ) 
        
        # Convert to List    #### Move this after for loop 
        leaderboard_list = [user for user in leaderboard]

        # Check if user should be added after top 10 displayed
        current_user = {}
        for user in leaderboard_list: # ###in leaderboard
            if (
                user["device_id"] == account_id
                and user["rank"] > leaderboard_length
            ):
                
                current_user = user

        # Cut list length to specified length (10)
        leaderboard_list = leaderboard_list[:leaderboard_length]


        # if ____
        leaderboard_list.append(current_user)




        # cut list to 10 items, add current user
        json_response["payload"]["leaderboard"] = leaderboard_list

        if current_contest is None:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "There are no contests",
                }
            )
        return JsonResponse(json_response)
