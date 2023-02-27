import logging

from django.db import connection
from django.db.models import Count, F, Q, Sum
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
        filters = {"is_tester": False}
        if request.user.is_authenticated:
            results = Account.objects.filter(**filters).aggregate(
                Sum("dailywalk__steps"),
                Sum("dailywalk__distance"),
            )
            payload = {
                "accounts_count": Account.objects.filter(**filters).count(),
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
            order_by = request.GET.get("order_by", "name")
            page = int(request.GET.get("page", "1"))
            per_page = 25

            # filter and annotate based on contest_id
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

            # filter to show users vs testers
            filters = filters & Q(
                is_tester=request.GET.get("is_tester", None) == "true"
            )

            # set ordering
            if order_by.startswith("-"):
                order_by = [F(order_by[1:]).desc(nulls_last=True)]
            else:
                order_by = [F(order_by).asc(nulls_first=False)]

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


class AdminUsersByZipView(View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        values = ["zip"]
        order_by = ["zip"]
        if request.user.is_authenticated:
            # filter and annotate based on contest_id
            filters = None
            annotate = {
                "count": Count("zip"),
            }
            contest_id = request.GET.get("contest_id", None)
            if contest_id:
                filters = Q(contests__contest_id=contest_id)
            else:
                filters = Q()

            # filter to show users vs testers
            filters = filters & Q(
                is_tester=request.GET.get("is_tester", None) == "true"
            )

            results = (
                Account.objects.filter(filters)
                .values(*values)
                .annotate(**annotate)
                .order_by(*order_by)
            )
            response = JsonResponse({r["zip"]: r["count"] for r in results})
            return response
        else:
            return HttpResponse(status=401)


class AdminUsersByZipMedianStepsView(View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            is_tester = request.GET.get("is_tester", None) == "true"
            contest_id = request.GET.get("contest_id", None)
            if contest_id is None:
                return HttpResponse(status=422)
            contest = Contest.objects.get(pk=contest_id)
            payload = {}
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY sum)
                    FROM (
                        SELECT home_account.id AS id, SUM(home_dailywalk.steps) AS sum
                        FROM home_account
                        JOIN home_dailywalk ON home_account.id=home_dailywalk.account_id
                        JOIN home_account_contests ON home_account.id=home_account_contests.account_id
                        WHERE home_account.is_tester=%s AND
                              home_account_contests.contest_id=%s AND
                              home_dailywalk.date BETWEEN %s AND %s
                        GROUP BY (home_account.id)
                    ) subquery
                """,
                    [is_tester, contest_id, contest.start, contest.end],
                )
                row = cursor.fetchone()

                payload["all"] = row[0]
                cursor.execute(
                    """
                    SELECT zip, PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY sum)
                    FROM (
                        SELECT home_account.id AS id, home_account.zip AS zip, SUM(home_dailywalk.steps) AS sum
                        FROM home_account
                        JOIN home_dailywalk ON home_account.id=home_dailywalk.account_id
                        JOIN home_account_contests ON home_account.id=home_account_contests.account_id
                        WHERE home_account.is_tester=%s AND
                              home_account_contests.contest_id=%s AND
                              home_dailywalk.date BETWEEN %s AND %s
                        GROUP BY (home_account.id, home_account.zip)
                    ) subquery
                    GROUP BY zip
                """,
                    [is_tester, contest_id, contest.start, contest.end],
                )
                rows = cursor.fetchall()
                for row in rows:
                    payload[row[0]] = row[1]

            response = JsonResponse(payload)
            return response
        else:
            return HttpResponse(status=401)
