from django.db.models import F
from django.db.models.expressions import Window
from django.db.models.functions import Rank
from django.views.decorators.csrf import csrf_exempt
from ninja import Router
from ninja.errors import HttpError

from home.models import Contest, Device, Leaderboard
from home.views.apiv2.schemas.leaderboard import ErrorSchema, LeaderboardSchema

router = Router()


@router.get("/get", response={200: LeaderboardSchema, 404: ErrorSchema})
@csrf_exempt
def get_leaderboard(request, contest_id: str, device_id: str):
    current_contest = Contest.objects.filter(contest_id=contest_id)
    if not current_contest:
        raise HttpError(404, "Contest not found")

    # http://localhost:8000/api/v2/leaderboard/
    # get?contest_id=<contest>&device_id=<device_id>

    # Validate request. If any field is missing,
    # send back the response message
    # Get the device if already registered
    try:
        device = Device.objects.get(device_id=device_id)
    except Device.DoesNotExist:
        raise HttpError(
            404, (
            f"Unregistered device - "
            f"{device_id}. "
            f"Please register first!"),
        )

    # Json response template
    json_response = {"leaderboard": []}

    leaderboard_list = []
    leaderboard_length = 10
    leaderboard = (
        Leaderboard.objects.filter(
            contest_id=contest_id,
            account__is_tester=device.account.is_tester,
        )
        .values("account_id", "steps")
        .annotate(rank=Window(expression=Rank(), order_by=F("steps").desc()))
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

    json_response["leaderboard"] = leaderboard_list

    return 200, json_response
