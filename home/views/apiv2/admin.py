import logging
import os
from datetime import timedelta
from typing import List

from dateutil import parser
from django.db import connection
from django.db.models import CharField, Count, Q, Sum, Value
from django.db.models.functions import Concat, TruncDate
from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from ninja import Query, Router
from ninja.errors import HttpError, ValidationError
from ninja.security import django_auth_superuser

from home.models import Account, Contest, DailyWalk
from home.views.api.utils import paginate

from .histogram.histogram import Histogram
from .schemas.admin import (
    AdminHomeSchema,
    AdminMeSchema,
    ContestOutSchema,
    ErrorSchema,
    HistogramInSchema,
    HistogramOutSchema,
    HomeGraphFilter,
    UsersByZipInSchema,
    UsersByZipOutSchema,
    UsersInSchema,
    UsersOutSchema,
)

logger = logging.getLogger(__name__)
router = Router()


@router.get("/me", response={200: AdminMeSchema, 204: None})
@csrf_exempt
def get_admin_me(request):
    if request.user.is_authenticated:
        return {
            "id": request.user.id,
            "username": request.user.username,
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "email": request.user.email,
        }
    else:
        return 204, None


@router.get(
    "/home",
    response={200: AdminHomeSchema},
    auth=django_auth_superuser,
)
@csrf_exempt
def get_admin_home(request):
    filters = {"is_tester": False}
    results = Account.objects.filter(**filters).aggregate(
        Sum("dailywalk__steps"),
        Sum("dailywalk__distance"),
    )
    payload = {
        "accounts_count": Account.objects.filter(**filters).count(),
        "accounts_steps": results["dailywalk__steps__sum"],
        "accounts_distance": results["dailywalk__distance__sum"],
    }
    return payload


def get_contest_start_end(qs: HomeGraphFilter) -> tuple[str, str]:
    # Handle common parameters for all the chart data API endpoints
    if qs.contest_id:
        try:
            contest = Contest.objects.get(pk=qs.contest_id)
            start_date = min(
                contest.start_baseline, contest.start_promo
            ).isoformat()
            end_date = contest.end.isoformat()
        except Contest.DoesNotExist:
            raise HttpError(
                404, f"Cannot find contest with contest_id {qs.contest_id}"
            )
    else:
        start_date, end_date = None, None

    return start_date, end_date


def process_results(
    results: list,
    start_date: str | None,
    end_date: str | None,
    is_cumulative: bool = False,
) -> list:
    # Handle common result processing for the chart data
    if len(results) > 0:
        if start_date and results[0][0] != f"{start_date}T00:00:00":
            results.insert(0, [f"{start_date}T00:00:00", 0])
        if end_date and results[-1][0] != f"{end_date}T00:00:00":
            if is_cumulative:
                results.append([f"{end_date}T00:00:00", results[-1][1]])
            else:
                results.append([f"{end_date}T00:00:00", 0])
    else:
        results.append([start_date, 0])
        results.append([end_date, 0])
    results.insert(0, ["Date", "Count"])

    return results


@router.get(
    "/home/users/daily",
    response={200: List, 404: ErrorSchema},
    auth=django_auth_superuser,
)
def get_users_daily(request, qs: Query[HomeGraphFilter]):
    start_date, end_date = get_contest_start_end(qs)
    filters = Q()
    # Filter to show users vs testers
    filters = filters & Q(is_tester=qs.is_tester)
    # Filter by date
    if start_date:
        filters = filters & Q(created__gte=start_date)
    if end_date:
        filters = filters & Q(
            created__lt=parser.parse(end_date) + timedelta(days=1)
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

    results = process_results(
        results, start_date, end_date, is_cumulative=False
    )

    return results


@router.get(
    "/home/users/cumulative",
    response={200: List, 404: ErrorSchema},
    auth=django_auth_superuser,
)
def get_users_cumulative(request, qs: Query[HomeGraphFilter]):
    start_date, end_date = get_contest_start_end(qs)
    conditions = """
            "is_tester"=%s
        """
    params = [qs.is_tester]
    if start_date:
        conditions = f"""{conditions} AND
                "created" >= %s
            """
        params.append(start_date)
    if end_date:
        conditions = f"""{conditions} AND
                "created" < %s
            """
        params.append(parser.parse(end_date) + timedelta(days=1))

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

    results = process_results(
        results, start_date, end_date, is_cumulative=True
    )

    return results


def get_results_walks_daily(
    start_date: str = None,
    end_date: str = None,
    is_tester: bool = False,
    value_type=None,
):
    filters = Q()
    # Filter to show users vs testers
    filters = filters & Q(account__is_tester=is_tester)
    # Filter by date
    if start_date:
        filters = filters & Q(date__gte=start_date)
    if end_date:
        filters = filters & Q(date__lte=end_date)
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
            count=Sum(value_type),
        )
        .order_by("date_time")
    )
    results = [[row["date_time"], row["count"]] for row in results]

    return results


@router.get(
    "/home/steps/daily",
    response={200: List, 404: ErrorSchema},
    auth=django_auth_superuser,
)
def get_walks_steps_daily(request, qs: Query[HomeGraphFilter]):
    start_date, end_date = get_contest_start_end(qs)
    results = get_results_walks_daily(
        start_date, end_date, qs.is_tester, "steps"
    )
    results = process_results(
        results, start_date, end_date, is_cumulative=False
    )

    return results


@router.get(
    "/home/distance/daily",
    response={200: List, 404: ErrorSchema},
    auth=django_auth_superuser,
)
def get_walks_distance_daily(request, qs: Query[HomeGraphFilter]):
    start_date, end_date = get_contest_start_end(qs)
    results = get_results_walks_daily(
        start_date, end_date, qs.is_tester, "distance"
    )
    results = process_results(
        results, start_date, end_date, is_cumulative=False
    )

    return results


def get_results_walks_cumulative(
    start_date: str = None,
    end_date: str = None,
    is_tester: bool = False,
    value_type=None,
):

    conditions = """
        "home_account"."is_tester"=%s
    """
    params = [is_tester]
    if start_date:
        conditions = f"""{conditions} AND
            "home_dailywalk"."date" >= %s
        """
        params.append(start_date)
    if end_date:
        conditions = f"""{conditions} AND
            "home_dailywalk"."date" <= %s
        """
        params.append(end_date)

    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT "date", (SUM("count") OVER (ORDER BY "date"))::int AS "count"
            FROM
                (SELECT
                    CONCAT("date", 'T00:00:00') AS "date",
                    SUM("{value_type}") AS "count"
                FROM "home_dailywalk"
                JOIN "home_account" ON "home_account"."id"="home_dailywalk"."account_id"
                WHERE {conditions}
                GROUP BY "date") subquery
            ORDER BY "date"
            """,
            params,
        )
        results = cursor.fetchall()

    return results


@router.get(
    "/home/steps/cumulative",
    response={200: List, 404: ErrorSchema},
    auth=django_auth_superuser,
)
def get_walks_steps_cumulative(request, qs: Query[HomeGraphFilter]):
    start_date, end_date = get_contest_start_end(qs)
    results = get_results_walks_cumulative(
        start_date,
        end_date,
        is_tester=qs.is_tester,
        value_type="steps",
    )
    results = process_results(
        results=results,
        start_date=start_date,
        end_date=end_date,
        is_cumulative=True,
    )

    return results


@router.get(
    "/home/distance/cumulative",
    response={200: List, 404: ErrorSchema},
    auth=django_auth_superuser,
)
def get_walks_distance_cumulative(request, qs: Query[HomeGraphFilter]):
    start_date, end_date = get_contest_start_end(qs)
    results = get_results_walks_cumulative(
        start_date,
        end_date,
        is_tester=qs.is_tester,
        value_type="distance",
    )
    results = process_results(
        results=results,
        start_date=start_date,
        end_date=end_date,
        is_cumulative=True,
    )

    return results


@router.get(
    "/users",
    response={200: UsersOutSchema},
    exclude_none=True,
    auth=django_auth_superuser,
)
def get_users(
    request: HttpRequest, response: HttpResponse, qs: Query[UsersInSchema]
):
    filters = qs.filter_dict["filters"]
    order_by = qs.filter_dict["order_by"]
    page = qs.filter_dict["page"]
    per_page = qs.filter_dict["per_page"]

    annotate = qs.filter_dict["annotate"]
    intentionalwalk_annotate = qs.filter_dict["intentionalwalk_annotate"]

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

    result_dto = [
        qs.update_user_dto(dto, iw_stat)
        for dto, iw_stat in zip(query, iw_query)
    ]

    if links:
        response.headers["Link"] = links

    return 200, {"users": result_dto}


@router.get(
    "/contests",
    response={200: List[ContestOutSchema]},
    auth=django_auth_superuser,
)
def get_contests(request):
    values = ["contest_id", "start", "end"]
    order_by = ["-start"]
    results = Contest.objects.values(*values).order_by(*order_by)

    return list(results)


@router.get(
    "/users/zip",
    response={200: UsersByZipOutSchema},
    exclude_none=True,
    auth=django_auth_superuser,
)
def get_users_by_zip(request, qs: Query[UsersByZipInSchema]):
    values = ["zip"]
    order_by = ["zip"]
    payload = {}
    # Filter and annotate based on contest_id
    filters = None
    annotate = {
        "count": Count("zip"),
    }
    contest_id = qs.contest_id
    if qs.contest_id:
        filters = Q(contests__contest_id=qs.contest_id)
    else:
        filters = Q()

    # Filter to show users vs testers
    filters = filters & Q(is_tester=qs.is_tester)

    # Query for totals
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

    return payload


@router.get(
    "users/zip/active",
    response={200: UsersByZipOutSchema, 404: ErrorSchema},
    auth=django_auth_superuser,
)
def get_users_zip_active(request, qs: Query[UsersByZipInSchema]):
    contest_id = qs.contest_id
    is_tester = qs.is_tester
    payload = {}
    try:
        contest = Contest.objects.get(pk=contest_id)
    except Contest.DoesNotExist:
        raise HttpError(404, f"Cannot find contest_id {contest_id}")

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

    return payload


@router.get(
    "users/zip/steps",
    response={200: dict[str, float | None], 404: ErrorSchema},
    exclude_none=False,
    auth=django_auth_superuser,
)
def get_users_by_zip_median(request, qs: Query[UsersByZipInSchema]):
    contest_id = qs.contest_id
    is_tester = qs.is_tester
    payload = {}
    try:
        contest = Contest.objects.get(pk=contest_id)
    except Contest.DoesNotExist:
        raise HttpError(404, f"Cannot find contest_id {contest_id}")

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

    return payload


@router.get(
    "{model}/histogram",
    response={200: HistogramOutSchema, 404: ErrorSchema, 422: ErrorSchema},
    exclude_none=True,
    auth=django_auth_superuser,
)
def get_model_histogram(
    request,
    model: str,
    qs: Query[HistogramInSchema],
):
    histogram = Histogram(model)
    if model not in histogram.supported_models:
        raise HttpError(
            404, f"Invalid model and/or {model} does not support histograms"
        )
    model = histogram.supported_models[model]

    valid_fields = histogram.supported_fields.get(model, [])
    if qs.field not in valid_fields:
        raise ValidationError(
            {
                "non_field_errors": f"{qs.field} is not supported for {model}. Please use one of {valid_fields}."
            }
        )

    histogram.set_unit(histogram.field_units.get(qs.field))
    contest = None
    if qs.contest_id:
        try:
            contest = Contest.objects.get(contest_id=qs.contest_id)
        except Contest.DoesNotExist:
            raise HttpError(
                404, f"Contest with id {qs.contest_id} does not exist."
            )
    histogram.set_unit(histogram.field_units.get(qs.field))

    res = histogram.create_bin_query(
        model=model,
        field=qs.field,
        is_tester=qs.is_tester,
        contest=contest,
        start_date=qs.start_date,
        end_date=qs.end_date,
        bin_count=qs.bin_count,
        bin_size=qs.bin_size,
        bin_custom=qs.bin_custom,
    )
    # Even bins either specified by bin_size or bin_size computed from bin_count
    if res.get("bin_size"):
        return 200, {
            "data": list(
                histogram.fill_missing_bin_idx(
                    query_set=res["query_set"],
                    bin_size=res["bin_size"],
                    total_bin_ct=res["bin_count"],
                )
            ),
            "unit": res["unit"],
            "bin_size": res["bin_size"],
        }

    # Custom bins
    return 200, {
        "data": list(
            histogram.fill_missing_bin_idx(
                query_set=res["query_set"],
                bin_custom=res["bin_custom"],
                total_bin_ct=res["bin_count"],
            )
        ),
        "unit": res["unit"],
        "bin_custom": res["bin_custom"],
    }
