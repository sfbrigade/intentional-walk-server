import json, logging

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
                .order_by(*order_by)
            )
            (results, links) = paginate(request, results, page, per_page)
            response = JsonResponse(list(results), safe=False)
            if links:
                response.headers["Link"] = links

            return response
        else:
            return HttpResponse(status=401)
