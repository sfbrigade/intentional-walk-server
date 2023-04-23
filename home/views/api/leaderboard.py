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
        device_id = request.GET.get("device_id")

        # Parse params
        if contest_id is None:
            return HttpResponse("No contest specified")

        current_contest = Contest.objects.filter(contest_id=contest_id)
        if current_contest is None:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Contest not found",
                }
            )

        # http://localhost:8000/api/leaderboard/
        # get?contest_id=<contest>?device_id=<device_id>

        # Validate request. If any field is missing,
        # send back the response message
        # Get the device if already registered
        device = None
        try:
            device = Device.objects.get(device_id=device_id)
        except ObjectDoesNotExist:
            return JsonResponse(
                {
                    "status": "error",
                    "message": (
                        "Unregistered device - "
                        "Please register first!"
                        "device_id:"
                        f"{device_id}"
                    ),
                }
            )

        # Json response template
        json_response = {
            "status": "success",
            "message": "Leaderboard accessed successfully",
            "payload": {
                "leaderboard": [],
            },
        }

        leaderboard_list = []
        leaderboard_length = 10
        leaderboard = (
            Leaderboard.objects.filter(
                contest_id=contest_id,
                account__is_tester=device.account.is_tester,
            )
            .values("account_id", "steps")
            .annotate(
                rank=Window(expression=Rank(), order_by=F("steps").desc())
            )
        )

        # get top 10
        leaderboard_list = list(leaderboard[0:leaderboard_length])

        # Check if user should be added after top 10 displayed
        eleventh_place = True
        for user in leaderboard_list:
            if user["account_id"] == device.account.id:
                user["device_id"] = device_id
                eleventh_place = False
                break

        # If user not in top 10, add as 11th in list
        if eleventh_place:
            leaderboard = Leaderboard.objects.filter(
                contest_id=contest_id, account=device.account
            ).values("account_id", "steps")
            if len(leaderboard) > 0:
                user = leaderboard[0]
                user["device_id"] = device_id
                user["rank"] = Leaderboard.objects.filter(
                    contest_id=contest_id,
                    steps__gte=user["steps"],
                    account__is_tester=device.account.is_tester,
                ).count()
                leaderboard_list.append(user)

        json_response["payload"]["leaderboard"] = leaderboard_list

        return JsonResponse(json_response)
