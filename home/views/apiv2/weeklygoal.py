from datetime import datetime

from django.views.decorators.csrf import csrf_exempt
from ninja import Router
from ninja.errors import HttpError

from home.models import Device, WeeklyGoal
from home.utils.dates import DATE_FORMAT, get_start_of_week
from home.views.apiv2.schemas.weeklygoal import (
    ErrorSchema,
    WeeklyGoalInSchema,
    WeeklyGoalListOutSchema,
    WeeklyGoalOutSchema,
)

router = Router()


@router.post("", response={201: WeeklyGoalOutSchema, 404: ErrorSchema})
@csrf_exempt
def create_weekly_goal(request, payload: WeeklyGoalInSchema):
    """Create or update a weeklygoal for an account"""
    json_data = payload.dict()
    # Get the device
    try:
        device = Device.objects.get(device_id=json_data["account_id"])
        account = device.account
    except Device.DoesNotExist:
        raise HttpError(
            404,
            (
                f"Unregistered device - "
                f"{json_data['account_id']}. "
                f"Please register first!"
            ),
        )

    # Json response template
    json_response = {"account_id": account.id, "weekly_goal": {}}

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
    except WeeklyGoal.DoesNotExist:
        # Creation if object is missing
        weekly_goal = WeeklyGoal.objects.create(
            start_of_week=start_of_week_update,
            steps=steps_update,
            days=days_update,
            account=account,
        )

    # Update the json object
    json_response["weekly_goal"] = {
        "start_of_week": weekly_goal.start_of_week,
        "steps": weekly_goal.steps,
        "days": weekly_goal.days,
    }
    return 201, json_response


@router.get(
    "/{account_id}", response={200: WeeklyGoalListOutSchema, 404: ErrorSchema}
)
@csrf_exempt
def get_weekly_goals(request, account_id: str):
    """Get List of Weekly Goals"""
    # Get the device
    try:
        device = Device.objects.get(device_id=account_id)
        account = device.account
    except Device.DoesNotExist:
        raise HttpError(
            404,
            (
                f"Unregistered account - "
                f"{account_id}. "
                f"Please register first!"
            ),
        )

    # Get weekly goals tied to this account
    weekly_goals = list(WeeklyGoal.objects.filter(account=account).values())
    """ for goal in weekly_goals:
        goal = model_to_dict(goal) """
    for goal in weekly_goals:
        goal["start_of_week"] = goal["start_of_week"].strftime(DATE_FORMAT)

    return 200, {"weekly_goals": weekly_goals}
