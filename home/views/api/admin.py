import logging

from django.db.models import Count, Q, Sum
from django.forms.models import model_to_dict
from django.http import HttpResponse, JsonResponse
from django.views import View

from home.models import Account, Contest

from .utils import paginate

logger = logging.getLogger(__name__)


class AdminMeView(View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return JsonResponse(model_to_dict(request.user))
        else:
            return HttpResponse(status=204)


class AdminHomeView(View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            results = Account.objects.aggregate(
                Sum("dailywalk__steps"),
                Sum("dailywalk__distance"),
            )
            payload = {
                "accounts_count": Account.objects.count(),
                "accounts_steps": results["dailywalk__steps__sum"],
                "accounts_distance": results["dailywalk__distance__sum"],
            }
            return JsonResponse(payload)
        else:
            return HttpResponse(status=204)


class AdminContestsView(View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            values = ["contest_id", "start", "end"]
            order_by = ["-start"]
            results = Contest.objects.values(*values).order_by(*order_by)
            return JsonResponse(list(results), safe=False)
        else:
            return HttpResponse(status=401)


class AdminUsersView(View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            values = ["id", "name", "email", "age", "zip", "created"]
            order_by = ["name"]
            page = int(request.GET.get("page", "1"))
            per_page = 25

            filters = None
            annotate = None
            contest_id = request.GET.get("contest_id", None)
            if contest_id:
                filters = Q(contests__contest_id=contest_id)
                contest = Contest.objects.get(pk=contest_id)
                dailywalk_filter = Q(
                    dailywalk__date__range=(contest.start, contest.end)
                )
                annotate = {
                    "dw_count": Count("dailywalk", filter=dailywalk_filter),
                    "dw_steps": Sum(
                        "dailywalk__steps", filter=dailywalk_filter
                    ),
                    "dw_distance": Sum(
                        "dailywalk__distance", filter=dailywalk_filter
                    ),
                }
            else:
                filters = Q()
                annotate = {
                    "dw_count": Count("dailywalk"),
                    "dw_steps": Sum("dailywalk__steps"),
                    "dw_distance": Sum("dailywalk__distance"),
                }

            results = (
                Account.objects.filter(filters)
                .values(*values)
                .annotate(**annotate)
                .order_by(*order_by)
            )
            (results, links) = paginate(request, results, page, per_page)

            response = JsonResponse(list(results), safe=False)
            if links:
                response.headers["Link"] = links

            return response
        else:
            return HttpResponse(status=401)
