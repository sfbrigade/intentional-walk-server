from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.utils.decorators import method_decorator

from home.models import Contest


@method_decorator(csrf_exempt, name="dispatch")
class ContestCurrentView(View):
    """View to retrieve current Contest
    """

    model = Contest
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        # get the current/next Contest
        contest = Contest.active()
        if contest is None:
            return JsonResponse({"status": "error", "message": f"There are no contests",})
        return JsonResponse(
            {
                "status": "success",
                "payload": {
                    "contest_id": contest.contest_id,
                    "start_baseline": contest.start_baseline,
                    "start_promo": contest.start_promo,
                    "start": contest.start,
                    "end": contest.end,
                },
            }
        )
