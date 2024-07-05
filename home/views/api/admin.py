import itertools
import logging
import os
from datetime import timedelta

from dateutil import parser
from django.db import connection
from django.db.models import CharField, Count, Q, Sum, Value
from django.db.models.functions import Concat, TruncDate
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views import View
from rest_framework import status
from rest_framework.response import Response

from home.models import Account, Contest, DailyWalk
from home.models.intentionalwalk import IntentionalWalk
from home.models.leaderboard import Leaderboard
from home.views.api.histogram.serializers import (
    HistogramReqSerializer,
    ValidatedHistogramReq,
)
from home.views.api.serializers.request_serializers import (
    GetUsersReqSerializer,
)
from home.views.api.serializers.response_serializers import (
    GetUsersRespSerializer,
)

from .utils import paginate, require_authn

logger = logging.getLogger(__name__)


class AdminMeView(View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return JsonResponse(
                {
                    "id": request.user.id,
                    "username": request.user.username,
                    "first_name": request.user.first_name,
                    "last_name": request.user.last_name,
                    "email": request.user.email,
                }
            )
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


class AdminHomeGraphView(View):
    http_method_names = ["get"]

    def is_cumulative(self):
        return False

    def get_results(self):
        return []

    def get(self, request, *args, **kwargs):
        # if not request.user.is_authenticated:
        #     return HttpResponse(status=401)

        # handle common parameters for all the chart data API endpoints
        contest_id = request.GET.get("contest_id", None)
        if contest_id:
            contest = Contest.objects.get(pk=contest_id)
            self.start_date = min(
                contest.start_baseline, contest.start_promo
            ).isoformat()
            self.end_date = contest.end.isoformat()
        else:
            self.start_date = request.GET.get("start_date", None)
            self.end_date = request.GET.get("end_date", None)
        self.is_tester = request.GET.get("is_tester", None) == "true"

        # let the concrete subclass implement the actual query
        results = self.get_results()

        # handle common result processing for the chart data
        if len(results) > 0:
            if (
                self.start_date
                and results[0][0] != f"{self.start_date}T00:00:00"
            ):
                results.insert(0, [f"{self.start_date}T00:00:00", 0])
            if self.end_date and results[-1][0] != f"{self.end_date}T00:00:00":
                if self.is_cumulative():
                    results.append(
                        [f"{self.end_date}T00:00:00", results[-1][1]]
                    )
                else:
                    results.append([f"{self.end_date}T00:00:00", 0])
        else:
            results.append([self.start_date, 0])
            results.append([self.end_date, 0])
        results.insert(0, ["Date", "Count"])
        return JsonResponse(results, safe=False)


class AdminHomeUsersDailyView(AdminHomeGraphView):
    def get_results(self):
        filters = Q()
        # filter to show users vs testers
        filters = filters & Q(is_tester=self.is_tester)
        # filter by date
        if self.start_date:
            filters = filters & Q(created__gte=self.start_date)
        if self.end_date:
            filters = filters & Q(
                created__lt=parser.parse(self.end_date) + timedelta(days=1)
            )
        results = (
            Account.objects.filter(filters)
            .annotate(
                date=Concat(
                    TruncDate("created"),
                    Value("T00:00:00"),
                    output_field=CharField(),
                )
            )
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )
        results = [[row["date"], row["count"]] for row in results]
        return results


class AdminHomeUsersCumulativeView(AdminHomeGraphView):
    def is_cumulative(self):
        return True

    def get_results(self):
        conditions = """
            "is_tester"=%s
        """
        params = [self.is_tester]
        if self.start_date:
            conditions = f"""{conditions} AND
                "created" >= %s
            """
            params.append(self.start_date)
        if self.end_date:
            conditions = f"""{conditions} AND
                "created" < %s
            """
            params.append(parser.parse(self.end_date) + timedelta(days=1))

        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT "date", (SUM("count") OVER (ORDER BY "date"))::int AS "count"
                FROM
                    (SELECT
                        CONCAT(("created" AT TIME ZONE '{os.getenv("TIME_ZONE", "America/Los_Angeles")}')::date,
                                'T00:00:00') AS "date",
                        COUNT("id") AS "count"
                     FROM "home_account"
                     WHERE {conditions}
                     GROUP BY "date") subquery
                ORDER BY "date"
                """,
                params,
            )
            results = cursor.fetchall()
        return list(results)


class AdminHomeWalksDailyView(AdminHomeGraphView):
    def get_value_type(self):
        return None

    def get_results(self):
        filters = Q()
        # filter to show users vs testers
        filters = filters & Q(account__is_tester=self.is_tester)
        # filter by date
        if self.start_date:
            filters = filters & Q(date__gte=self.start_date)
        if self.end_date:
            filters = filters & Q(date__lte=self.end_date)
        results = (
            DailyWalk.objects.filter(filters)
            .annotate(
                date_time=Concat(
                    "date",
                    Value("T00:00:00"),
                    output_field=CharField(),
                ),
            )
            .values("date_time")
            .annotate(
                count=Sum(self.get_value_type()),
            )
            .order_by("date_time")
        )
        results = [[row["date_time"], row["count"]] for row in results]
        return results


class AdminHomeStepsDailyView(AdminHomeWalksDailyView):
    def get_value_type(self):
        return "steps"


class AdminHomeDistanceDailyView(AdminHomeWalksDailyView):
    def get_value_type(self):
        return "distance"


class AdminHomeWalksCumulativeView(AdminHomeGraphView):
    def is_cumulative(self):
        return True

    def get_value_type(self):
        return None

    def get_results(self):
        conditions = """
            "home_account"."is_tester"=%s
        """
        params = [self.is_tester]
        if self.start_date:
            conditions = f"""{conditions} AND
                "home_dailywalk"."date" >= %s
            """
            params.append(self.start_date)
        if self.end_date:
            conditions = f"""{conditions} AND
                "home_dailywalk"."date" <= %s
            """
            params.append(self.end_date)

        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT "date", (SUM("count") OVER (ORDER BY "date"))::int AS "count"
                FROM
                    (SELECT
                        CONCAT("date", 'T00:00:00') AS "date",
                        SUM("{self.get_value_type()}") AS "count"
                     FROM "home_dailywalk"
                     JOIN "home_account" ON "home_account"."id"="home_dailywalk"."account_id"
                     WHERE {conditions}
                     GROUP BY "date") subquery
                ORDER BY "date"
                """,
                params,
            )
            results = cursor.fetchall()
        results = list(results)
        return results


class AdminHomeStepsCumulativeView(AdminHomeWalksCumulativeView):
    def get_value_type(self):
        return "steps"


class AdminHomeDistanceCumulativeView(AdminHomeWalksCumulativeView):
    def get_value_type(self):
        return "distance"


class AdminContestsView(View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        # if request.user.is_authenticated:
        values = ["contest_id", "start", "end"]
        order_by = ["-start"]
        results = Contest.objects.values(*values).order_by(*order_by)
        return JsonResponse(list(results), safe=False)
        # else:
        #     return HttpResponse(status=401)


class AdminUsersView(View):
    http_method_names = ["get"]

    @require_authn
    def get(self, request, *args, **kwargs):
        serializer = GetUsersReqSerializer(data=request.GET)
        if not serializer.is_valid():
            return JsonResponse(serializer.errors, status=422)

        validated = serializer.validated_data

        contest_id = validated["contest_id"]
        filters = validated["filters"]
        order_by = validated["order_by"]
        page = validated["page"]
        per_page = validated["per_page"]

        annotate = validated["annotate"]
        intentionalwalk_annotate = validated["intentionalwalk_annotate"]

        query = (
            Account.objects.filter(filters)
            .values("id", "name", "email", "age", "zip", "created")
            .annotate(**annotate)
            .order_by(*order_by)
        )
        query, links = paginate(request, query, page, per_page)

        iw_query = (
            Account.objects.filter(id__in=(row["id"] for row in query))
            .values("id")
            .annotate(**intentionalwalk_annotate)
            .order_by(*order_by)
        )

        def update_user_dto(dto, iw_stats):
            dto.update(iw_stats)
            # at this point, we have enough info to determine if user is "active"
            if contest_id:
                dto["is_active"] = dto["dw_count"] > 0 or dto["iw_count"] > 0
            return dto

        result_dto = [
            update_user_dto(dto, iw_stat)
            for dto, iw_stat in zip(query, iw_query)
        ]
        resp = GetUsersRespSerializer(result_dto, many=True)
        response = JsonResponse(resp.data, safe=False)

        if links:
            response.headers["Link"] = links

        return response


class AdminUsersByZipView(View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        values = ["zip"]
        order_by = ["zip"]
        if request.user.is_authenticated:
            payload = {}
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

            # query for totals
            results = (
                Account.objects.filter(filters)
                .values(*values)
                .annotate(**annotate)
                .order_by(*order_by)
            )
            payload["total"] = {r["zip"]: r["count"] for r in results}

            # now query for new if for contest
            if contest_id:
                contest = Contest.objects.get(pk=contest_id)
                filters = filters & Q(
                    created__gte=contest.start_promo,
                    created__lt=contest.end + timedelta(days=1),
                )
                results = (
                    Account.objects.filter(filters)
                    .values(*values)
                    .annotate(**annotate)
                    .order_by(*order_by)
                )
                payload["new"] = {r["zip"]: r["count"] for r in results}

            return JsonResponse(payload)
        else:
            return HttpResponse(status=401)


class AdminUsersActiveByZipView(View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        contest_id = request.GET.get("contest_id", None)
        is_tester = request.GET.get("is_tester", None) == "true"
        if not contest_id:
            return HttpResponse(status=422)
        elif request.user.is_authenticated:
            payload = {}
            contest = Contest.objects.get(pk=contest_id)

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT zip, COUNT(*)
                    FROM (
                        SELECT DISTINCT(home_account.id), home_account.zip
                        FROM home_account
                        JOIN home_account_contests ON home_account.id=home_account_contests.account_id
                        LEFT JOIN home_dailywalk ON home_account.id=home_dailywalk.account_id
                        LEFT JOIN home_intentionalwalk ON home_account.id=home_intentionalwalk.account_id
                        WHERE home_account.is_tester=%s AND
                              home_account_contests.contest_id=%s AND
                              ((home_dailywalk.id IS NOT NULL AND home_dailywalk.date BETWEEN %s AND %s) OR
                               (home_intentionalwalk.id IS NOT NULL AND
                                home_intentionalwalk.start >= %s AND home_intentionalwalk.start < %s))
                    ) subquery
                    GROUP BY zip
                """,
                    [
                        is_tester,
                        contest_id,
                        contest.start,
                        contest.end,
                        contest.start,
                        contest.end + timedelta(days=1),
                    ],
                )
                rows = cursor.fetchall()
                payload["total"] = {row[0]: row[1] for row in rows}
                cursor.execute(
                    """
                    SELECT zip, COUNT(*)
                    FROM (
                        SELECT DISTINCT(home_account.id), home_account.zip
                        FROM home_account
                        JOIN home_account_contests ON home_account.id=home_account_contests.account_id
                        LEFT JOIN home_dailywalk ON home_account.id=home_dailywalk.account_id
                        LEFT JOIN home_intentionalwalk ON home_account.id=home_intentionalwalk.account_id
                        WHERE home_account.is_tester=%s AND
                              home_account_contests.contest_id=%s AND
                              home_account.created >= %s AND home_account.created < %s AND
                              ((home_dailywalk.id IS NOT NULL AND home_dailywalk.date BETWEEN %s AND %s) OR
                               (home_intentionalwalk.id IS NOT NULL AND
                                home_intentionalwalk.start >= %s AND home_intentionalwalk.start < %s))
                    ) subquery
                    GROUP BY zip
                """,
                    [
                        is_tester,
                        contest_id,
                        contest.start_promo,
                        contest.end + timedelta(days=1),
                        contest.start,
                        contest.end,
                        contest.start,
                        contest.end + timedelta(days=1),
                    ],
                )
                rows = cursor.fetchall()
                payload["new"] = {row[0]: row[1] for row in rows}

            return JsonResponse(payload)
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


class AdminHistogramView(View):
    http_method_names = ["get"]

    supported_models = {
        "users": Account,
        "dailywalk": DailyWalk,
        "intentionalwalk": IntentionalWalk,
        "leaderboard": Leaderboard,
    }

    @require_authn
    def get(self, request: HttpRequest, model_name: str) -> HttpResponse:
        """Get histogram data for a given model across a numberic field.

        Binning is done by the bin_size parameter, bin_count parameter,
        or bin_custom parameter.

        bin_size: The size of each bin.
        bin_count: The total number of bins.
        bin_custom: A comma separated list of bin edges.
        """
        if model_name not in self.supported_models:
            return HttpResponse(status=404)

        serializer = HistogramReqSerializer(
            data=request.GET, model=self.supported_models[model_name]
        )
        if not serializer.is_valid():
            return JsonResponse(serializer.errors, status=422)

        # TODO: Implement a ResponseSerializer
        # to handle serialization of the response
        # (with filling of the bins)
        # to either JSON or CSV format.
        res: ValidatedHistogramReq = serializer.validated_data

        # even bins either specified by bin_size or bin_size computed from bin_count
        if res.get("bin_size"):
            return JsonResponse(
                {
                    "data": list(
                        self.fill_missing_bin_idx(
                            query_set=res["query_set"],
                            bin_size=res["bin_size"],
                            total_bin_ct=res["bin_count"],
                        )
                    ),
                    "unit": res["unit"],
                    "bin_size": res["bin_size"],
                }
            )
        # custom bins
        return JsonResponse(
            {
                "data": list(
                    self.fill_missing_bin_idx(
                        query_set=res["query_set"],
                        bin_custom=res["bin_custom"],
                        total_bin_ct=res["bin_count"],
                    )
                ),
                "unit": res["unit"],
                "bin_custom": res["bin_custom"],
            }
        )

    def fill_missing_bin_idx(
        self,
        query_set,
        bin_size: int = None,
        bin_custom: list = None,
        total_bin_ct: int = 0,
    ):
        """Fill in missing bin intervals lazily.

        This is because the histogram is generated from a query set that may not have
        found data in certain bins.

        For example, if the bins were [0, 18, 20, 33, 50, 70],
        which creates bins from 0-17, 18-20, 20-33, 33-50, 50-70.

        There may be no users in in the 18-20 range, and no users in the 51 and 70.
        In other words, missing on bin_idx = 1 and bin_idx = 4.
        The query would not return any groupings for the [18, 20], or [50, 70]
        This function will fill in those missing bins with a count of 0.
        """

        def create_filler(cursor, bin_size, bin_custom):
            res = {}
            # bin_start and bin_end are inclusive.
            if bin_custom:
                res["bin_start"] = bin_custom[cursor]
                if cursor + 1 < len(bin_custom):
                    res["bin_end"] = bin_custom[cursor + 1]
            else:
                res["bin_start"] = cursor * bin_size
                res["bin_end"] = (cursor + 1) * bin_size
            # Done down here to maintain stable order of keys.
            res["count"] = 0
            res["bin_idx"] = cursor
            return res

        bin_idx_counter = itertools.count()
        cursor = 0
        for bin in query_set:
            cursor = next(bin_idx_counter)
            curr_idx = bin["bin_idx"]
            while curr_idx > cursor:
                yield create_filler(
                    cursor=cursor, bin_size=bin_size, bin_custom=bin_custom
                )
                cursor = next(bin_idx_counter)
            yield bin

        cursor = next(bin_idx_counter)
        # Fill in the rest of the bins with 0 count,
        # until we reach the total expected count of bins.
        while cursor and cursor < total_bin_ct:
            yield create_filler(
                cursor=cursor, bin_size=bin_size, bin_custom=bin_custom
            )
            cursor = next(bin_idx_counter)
