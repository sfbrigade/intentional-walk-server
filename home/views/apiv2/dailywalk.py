import logging
from datetime import date

from django.views.decorators.csrf import csrf_exempt
from ninja import Router
from ninja.errors import HttpError

from home.models import Contest, DailyWalk, Device
from home.views.apiv2.schemas.dailywalk import (
    DailyWalkInSchema,
    DailyWalkOutSchema,
    ErrorSchema,
)

logger = logging.getLogger(__name__)
router = Router()


@router.get(
    "/{account_id}", response={200: DailyWalkOutSchema, 404: ErrorSchema}
)
@csrf_exempt
def get_daily_walks(request, account_id: str):
    try:
        device = Device.objects.get(device_id=account_id)
    except Device.DoesNotExist:
        raise HttpError(
            404,
            (
                f"Unregistered device - "
                f"{account_id}. "
                f"Please register first!"
            ),
        )

    # Get walks from tied to this account
    # NOTE: This is very hacky and cannot distinguish between legit and
    # fake users.
    # Someone can simply install the app on a new device and use a known
    # email id and have the metrics simply aggregated.
    # For the simple use case, this is likely not an issue and would need
    # to be handled manually if needed
    daily_walks = DailyWalk.objects.filter(account=device.account)
    return 200, {"daily_walks": list(daily_walks)}


@router.post("", response={201: DailyWalkInSchema})
@csrf_exempt
def create_daily_walk(request, payload: DailyWalkInSchema):
    json_data = payload.dict()
    try:
        device = Device.objects.get(device_id=json_data["account_id"])
    except Device.DoesNotExist:
        raise HttpError(
            404,
            (
                f"Unregistered device - "
                f"{json_data['account_id']}. "
                f"Please register first!"
            ),
        )
    active_contests = set()

    # Json response template
    json_response = {
        "account_id": device.device_id,
        "daily_walks": [],
    }

    for daily_walk_data in json_data["daily_walks"]:
        walk_date = daily_walk_data["date"]
        contest = Contest.active(
            for_date=date.fromisoformat(walk_date), strict=True
        )
        if contest is not None:
            active_contests.add(contest)

        # Check if there is already an entry for this date. If there is,
        # update the entry.
        # NOTE: By definition, there should be one and only one entry for
        # a given email and date.
        # NOTE: This is a potential vulnerability. Since there is no email
        # authentication at the moment, anyone can simply spoof an email
        # id with a new device and overwrite daily walk data for the
        # target email. This is also a result of no session auth
        # (can easily hit the api directly)
        try:
            # Updation
            daily_walk = DailyWalk.objects.get(
                account=device.account, date=walk_date
            )
            daily_walk.steps = daily_walk_data["steps"]
            daily_walk.distance = daily_walk_data["distance"]
            daily_walk.device_id = json_data["account_id"]
            daily_walk.save()
        except DailyWalk.DoesNotExist:
            # Create if object is missing
            daily_walk = DailyWalk.objects.create(
                date=walk_date,
                steps=daily_walk_data["steps"],
                distance=daily_walk_data["distance"],
                device=device,
            )

        # Update the json response object
        json_response["daily_walks"].append(
            {
                "date": daily_walk.date,
                "steps": daily_walk.steps,
                "distance": daily_walk.distance,
            }
        )

    # Register contest for account if the day falls between contest dates
    contest = Contest.active(for_date=date.today(), strict=True)
    if contest:
        active_contests.add(contest)
        try:
            acct = device.account
            acct.contests.add(contest)
        except Exception:
            logger.error(
                f"Could not associate contest "
                f"{contest} with account {acct}!",
                exc_info=True,
            )
    else:
        # No active contest
        pass

    # Update Leaderboard
    for contest in active_contests:
        DailyWalk.update_leaderboard(device=device, contest=contest)

    return 201, json_response
