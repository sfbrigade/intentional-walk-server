import json

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from home.models import Contest, IntentionalWalk
from home.utils import localize

from .utils import validate_request_json

STEPS_PER_COIN = 2000
COINS_PER_BADGE = 5
STEPS_PER_BADGE = STEPS_PER_COIN * COINS_PER_BADGE


@method_decorator(csrf_exempt, name="dispatch")
class CurrencyView(View):
    """
    Retrieve data regarding an account's gamified currency.

    Gamificiation:
    - 2000 steps are worth 1 "coin"
    - 5 "coins" are worth 1 "badge"
    """

    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        json_data = json.loads(request.body)

        json_status = validate_request_json(
            json_data,
            required_fields=["account_id"],
        )
        if "status" in json_status and json_status["status"] == "error":
            return JsonResponse(json_status)

        # get the current/next Contest
        contest = Contest.active()
        if contest is None:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "There is no active contest",
                }
            )

        device_id = json_data["account_id"]
        walks = IntentionalWalk.objects.filter(
            start__gte=localize(contest.start),
            end__lte=localize(contest.end),
            device=device_id,
        ).values("steps")
        steps = sum(walk["steps"] for walk in walks)

        badges = max(int(steps / STEPS_PER_BADGE), 0)

        leftover_steps = max(steps - (badges * STEPS_PER_BADGE), 0)
        coins = int(leftover_steps / STEPS_PER_COIN)

        return JsonResponse(
            {
                "status": "success",
                "payload": {
                    "contest_id": contest.contest_id,
                    "account_id": device_id,
                    "steps": steps,
                    "coins": coins,
                    "badges": badges,
                },
            }
        )
