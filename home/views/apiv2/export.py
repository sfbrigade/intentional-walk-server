import csv
import logging
import os
import tempfile
from datetime import timedelta

from django.db.models import BooleanField, Count, ExpressionWrapper, Q, Sum
from django.http import FileResponse, HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from ninja import Router

from home.models import Account, Contest, DailyWalk

logger = logging.getLogger(__name__)
router = Router()

# configure the base CSV headers
CSV_COLUMNS = [
    {"name": "Participant Name", "id": "name"},
    {"name": "Date Enrolled", "id": "created"},
    {"name": "Email", "id": "email"},
    {"name": "Zip Code", "id": "zip"},
    {"name": "Sexual Orientation", "id": "sexual_orien"},
    {"name": "Sexual Orientation Other", "id": "sexual_orien_other"},
    {"name": "Gender Identity", "id": "gender"},
    {"name": "Gender Identity Other", "id": "gender_other"},
    {"name": "Race", "id": "race"},
    {"name": "Race Other", "id": "race_other"},
    {"name": "Is Latino", "id": "is_latino"},
    {"name": "Age", "id": "age"},
    {"name": "Is New Signup", "id": "is_new"},
    {"name": "Active During Contest", "id": "is_active"},
    {"name": "Total Daily Walks During Contest", "id": "dw_contest_count"},
    {
        "name": "Total Daily Walks During Baseline",
        "id": "dw_baseline_count",
    },
    {"name": "Total Steps During Contest", "id": "dw_contest_steps"},
    {"name": "Total Steps During Baseline", "id": "dw_baseline_steps"},
    {
        "name": "Total Recorded Walks During Contest",
        "id": "iw_contest_count",
    },
    {
        "name": "Total Recorded Walks During Baseline",
        "id": "iw_baseline_count",
    },
    {
        "name": "Total Recorded Steps During Contest",
        "id": "iw_contest_steps",
    },
    {
        "name": "Total Recorded Steps During Baseline",
        "id": "iw_baseline_steps",
    },
    {
        "name": "Total Recorded Walk Time During Contest",
        "id": "iw_contest_time",
    },
    {
        "name": "Total Recorded Walk Time During Baseline",
        "id": "iw_baseline_time",
    },
]


def get_dailywalk_stats(name, ids, dailywalk_filter):
    filters = Q(id__in=ids)
    values = ["id"]
    annotate = {
        f"dw_{name}_count": Count("dailywalk", filter=dailywalk_filter),
        f"dw_{name}_steps": Sum("dailywalk__steps", filter=dailywalk_filter),
        f"dw_{name}_distance": Sum(
            "dailywalk__distance", filter=dailywalk_filter
        ),
    }
    order_by = ["id"]
    return (
        Account.objects.filter(filters)
        .values(*values)
        .annotate(**annotate)
        .order_by(*order_by)
    )


def get_intentionalwalk_stats(name, ids, intentionalwalk_filter):
    filters = Q(id__in=ids)
    values = ["id"]
    annotate = {
        f"iw_{name}_count": Count(
            "intentionalwalk", filter=intentionalwalk_filter
        ),
        f"iw_{name}_steps": Sum(
            "intentionalwalk__steps", filter=intentionalwalk_filter
        ),
        f"iw_{name}_distance": Sum(
            "intentionalwalk__distance", filter=intentionalwalk_filter
        ),
        f"iw_{name}_time": Sum(
            "intentionalwalk__walk_time", filter=intentionalwalk_filter
        ),
    }
    order_by = ["id"]
    return (
        Account.objects.filter(filters)
        .values(*values)
        .annotate(**annotate)
        .order_by(*order_by)
    )


def get_daily_walks(ids, contest):
    filters = Q(
        account_id__in=ids, date__range=(contest.start_baseline, contest.end)
    )
    values = ["account_id", "date", "steps"]
    order_by = ["account_id", "date"]
    return (
        DailyWalk.objects.filter(filters).values(*values).order_by(*order_by)
    )


def export_contest_users_data(file, contest_id, is_tester):
    # get the Contest object
    contest = Contest.objects.get(pk=contest_id)

    # configure the CSV writer
    fieldnames = [col["id"] for col in CSV_COLUMNS]
    header = {col["id"]: col["name"] for col in CSV_COLUMNS}
    # add headers for every day in the output range (start of baseline to end of contest)
    for dt in range((contest.end - contest.start_baseline).days + 1):
        date = contest.start_baseline + timedelta(days=dt)
        fieldnames.append(str(date))
        header[str(date)] = str(date)
    writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
    writer.writerow(header)

    # query for the base attributes
    filters = Q(contests__contest_id=contest_id, is_tester=is_tester)
    values = [
        "id",
        "created",
        "name",
        "email",
        "age",
        "zip",
        "gender",
        "gender_other",
        "sexual_orien",
        "sexual_orien_other",
        "race",
        "race_other",
        "is_latino",
    ]
    annotate = {
        "is_new": ExpressionWrapper(
            Q(
                created__gte=contest.start_promo,
                created__lt=contest.end + timedelta(days=1),
            ),
            output_field=BooleanField(),
        ),
    }
    order_by = ["id"]
    results = (
        Account.objects.filter(filters)
        .values(*values)
        .annotate(**annotate)
        .order_by(*order_by)
    )

    # set up to process in batches
    offset = 0
    limit = 25
    total = results.count()
    while offset < total:
        ids = []
        rows = []
        for row in results[offset : offset + limit]:  # noqa E203
            # convert race Set into a comma delimited string
            row["race"] = ",".join(row["race"])
            # gather all rows and ids
            rows.append(row)
            ids.append(row["id"])
        offset = offset + limit

        # add in the baseline period dailywalk stats
        dw_baseline_results = get_dailywalk_stats(
            "baseline",
            ids,
            Q(
                dailywalk__date__range=(
                    contest.start_baseline,
                    contest.start - timedelta(days=1),
                )
            ),
        )
        for i, row in enumerate(dw_baseline_results):
            rows[i].update(row)

        # add in the contest period dailywalk stats
        dw_contest_results = get_dailywalk_stats(
            "contest",
            ids,
            Q(dailywalk__date__range=(contest.start, contest.end)),
        )
        for i, row in enumerate(dw_contest_results):
            rows[i].update(row)

        # add in the baseline period intentionalwalk stats
        iw_baseline_results = get_intentionalwalk_stats(
            "baseline",
            ids,
            Q(
                intentionalwalk__start__gte=contest.start_baseline,
                intentionalwalk__start__lt=contest.start,
            ),
        )
        for i, row in enumerate(iw_baseline_results):
            rows[i].update(row)

        # add in the contest period intentionalwalk stats
        iw_contest_results = get_intentionalwalk_stats(
            "contest",
            ids,
            Q(
                intentionalwalk__start__gte=contest.start,
                intentionalwalk__start__lt=contest.end + timedelta(days=1),
            ),
        )
        for i, row in enumerate(iw_contest_results):
            rows[i].update(row)
            # at this point, we have enough info to determine if user is "active"
            rows[i]["is_active"] = (
                rows[i]["dw_contest_count"] > 0
                or rows[i]["iw_contest_count"] > 0
            )

        # now add in every day of step data for each user
        daily_walks = get_daily_walks(ids, contest)
        rows_iter = iter(rows)
        account = next(rows_iter)
        for row in daily_walks:
            while row["account_id"] != account["id"]:
                account = next(rows_iter)
            account[str(row["date"])] = row["steps"]

        # finally, write it out to the CSV...!
        writer.writerows(rows)


@router.get("/users")
@csrf_exempt
def export_users(request, contest_id: str, is_tester: str):
    is_tester = is_tester == "true"

    if not contest_id:
        return HttpResponse(status=422)
    elif not request.user.is_authenticated:
        return HttpResponse(status=401)

    try:
        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        with open(tmp_file.name, "w") as file:
            export_contest_users_data(file, contest_id, is_tester)
        return FileResponse(
            open(tmp_file.name, "rb"),
            as_attachment=True,
            filename="users_agg.csv",
        )
    finally:
        os.remove(tmp_file.name)
