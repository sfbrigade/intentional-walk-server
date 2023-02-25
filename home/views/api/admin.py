import logging

from django.db.models import Count, Sum
from django.forms.models import model_to_dict
from django.http import HttpResponse, JsonResponse
from django.views import View

from home.models import Account

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


class AdminUsersView(View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            filters = {}
            values = ["id", "name", "email", "age", "zip", "created"]
            order_by = ["name"]
            page = int(request.GET.get("page", "1"))
            per_page = 25

            results = (
                Account.objects.filter(**filters)
                .values(*values)
                .annotate(
                    dw_count=Count("dailywalk"),
                    dw_steps=Sum("dailywalk__steps"),
                    dw_distance=Sum("dailywalk__distance"),
                )
                .order_by(*order_by)
            )
            (results, links) = paginate(request, results, page, per_page)

            response = JsonResponse(list(results), safe=False)
            if links:
                response.headers["Link"] = links

            return response
        else:
            return HttpResponse(status=401)
