import logging

from datetime import timedelta
from dateutil import parser

from django.db import connection
from django.db.models import BooleanField, Count, ExpressionWrapper, F, Q, Sum
from django.db.models.functions import TruncDate
from django.forms.models import model_to_dict
from django.http import HttpResponse, JsonResponse
from django.views import View

from home.models import Account, Contest, DailyWalk

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


class AdminHomeGraphView(View):
    http_method_names = ["get"]

    def is_cumulative(self):
        return False

    def get_results(self):
        return []

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponse(status=401)

        # handle common parameters for all the chart data API endpoints
        contest_id = request.GET.get("contest_id", None)
        if contest_id:
            contest = Contest.objects.get(pk=contest_id)
            self.start_date = contest.start_promo.isoformat()
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
                and results[0][0].isoformat() != self.start_date
            ):
                results.insert(0, [self.start_date, 0])
            if self.end_date and results[-1][0].isoformat() != self.end_date:
                if self.is_cumulative():
                    results.append([self.end_date, results[-1][1]])
                else:
                    results.append([self.end_date, 0])
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
            .annotate(date=TruncDate("created"))
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
                        ("created" AT TIME ZONE 'America/Los_Angeles')::date AS "date",
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
            .values("date")
            .annotate(count=Sum(self.get_value_type()))
            .order_by("date")
        )
        results = [[row["date"], row["count"]] for row in results]
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
                        "date",
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
            intentionalwalk_filter = None
            if contest_id:
                filters = Q(contests__contest_id=contest_id)
                contest = Contest.objects.get(pk=contest_id)
                dailywalk_filter = Q(
                    dailywalk__date__range=(contest.start, contest.end)
                )
                intentionalwalk_filter = Q(
                    intentionalwalk__start__gte=contest.start,
                    intentionalwalk__start__lt=contest.end + timedelta(days=1),
                )
                annotate = {
                    "is_new": ExpressionWrapper(
                        Q(
                            created__gte=contest.start_promo,
                            created__lt=contest.end + timedelta(days=1),
                        ),
                        output_field=BooleanField(),
                    ),
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
                intentionalwalk_filter = Q()

            # filter to show users vs testers
            filters = filters & Q(
                is_tester=request.GET.get("is_tester", None) == "true"
            )

            # filter by search query
            query = request.GET.get("query", None)
            if query:
                filters = filters & Q(
                    Q(name__icontains=query) | Q(email__icontains=query)
                )

            # set ordering
            add_name = False
            if order_by.startswith("-"):
                add_name = order_by[1:] != "name"
                order_by = [F(order_by[1:]).desc(nulls_last=True)]
            else:
                add_name = order_by != "name"
                order_by = [F(order_by).asc(nulls_first=False)]
            if add_name:
                order_by.append("name")

            # perform query!
            results = (
                Account.objects.filter(filters)
                .values(*values)
                .annotate(**annotate)
                .order_by(*order_by)
            )
            (results, links) = paginate(request, results, page, per_page)
            results = list(results)

            # now query for and add in recorded IntentionalWalk stats
            ids = [row["id"] for row in results]
            iw_results = (
                Account.objects.filter(id__in=ids)
                .values("id")
                .annotate(
                    iw_count=Count(
                        "intentionalwalk", filter=intentionalwalk_filter
                    ),
                    iw_steps=Sum(
                        "intentionalwalk__steps", filter=intentionalwalk_filter
                    ),
                    iw_distance=Sum(
                        "intentionalwalk__distance",
                        filter=intentionalwalk_filter,
                    ),
                    iw_time=Sum(
                        "intentionalwalk__walk_time",
                        filter=intentionalwalk_filter,
                    ),
                )
                .order_by(*order_by)
            )
            for i, row in enumerate(iw_results):
                results[i].update(row)
                # at this point, we have enough info to determine if user is "active"
                if contest_id:
                    results[i]["is_active"] = (
                        results[i]["dw_count"] > 0
                        or results[i]["iw_count"] > 0
                    )

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
