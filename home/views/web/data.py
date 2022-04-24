import csv
import logging

from collections import defaultdict
from datetime import date, timedelta
from django.http import HttpResponse

from home.models import Account, Contest
from home.utils import localize
from home.views.web.user import ACCOUNT_FIELDS, get_contest_walks, get_new_signups, get_daily_walks_in_time_range


logger = logging.getLogger(__name__)


USER_AGG_CSV_BASE_HEADER = [
    "Participant Name", "Date Enrolled", "Email", "Zip Code",
    "Sexual Orientation", "Sexual Orientation Other",
    "Gender Identity", "Gender Identity Other",
    "Race", "Race Other",
    "Is Latino", "Age", "Is New Signup", "Active During Contest",
    "Total Daily Walks During Contest", "Total Daily Walks During Baseline",
    "Total Steps During Contest", "Total Steps During Baseline",
    "Total Recorded Walks During Contest", "Total Recorded Walks During Baseline",
    "Total Recorded Steps During Contest", "Total Recorded Steps During Baseline",    
    "Total Recorded Walk Time During Contest", "Total Recorded Walk Time During Baseline",    
]


def yesno(value: bool) -> str:
    return "yes" if value else "no"


def _get_user_agg_csv_header(start_date: date, end_date: date) -> list:
    header = USER_AGG_CSV_BASE_HEADER[:]

    baseline_and_contest_dates = [
        start_date+timedelta(days=x)
        for x in range((end_date - start_date).days + 1)
    ]
    
    for d in baseline_and_contest_dates:
        header.append(d)

    return header


def _acct_to_row_data(
    acct: dict, 
    new_signup_emails: set,
    active_during_contest: bool
) -> dict:
    return {
        "Participant Name": acct["name"],
        "Date Enrolled": acct["created"],
        "Email": acct["email"],
        "Zip Code": acct["zip"],
        "Sexual Orientation": acct["sexual_orien"],
        "Sexual Orientation Other": acct["sexual_orien_other"],
        "Gender Identity": acct["gender"],
        "Gender Identity Other": acct["gender_other"],
        "Race": acct["race"],
        "Race Other": acct["race_other"],
        "Is Latino": acct["is_latino"],
        "Age": acct["age"],
        "Is New Signup": yesno(acct["email"] in new_signup_emails),
        "Active During Contest": yesno(active_during_contest),
     }


def _get_rows_for_new_signups_without_walks(contest: Contest, user_emails_with_walks: set, new_signups: dict) -> list:
    rows = []
    for acct in new_signups.values():
        if acct["email"] not in user_emails_with_walks:
            row_data = _acct_to_row_data(
                acct, new_signups, active_during_contest=False)
            rows.append(row_data)

    return rows


def _get_user_summary_acct_and_walk_data(
        contest: Contest,
        user_emails: set,
        new_signup_emails: set,
        daily_walks_summary_contest: dict,
        intentional_walks_summary_contest: dict,
        daily_walks_summary_baseline: dict,
        intentional_walks_summary_baseline: dict,
) -> dict:
    summary_acct_and_walk_data_per_user = defaultdict(dict)

    # Add all accounts found in filtered walk summary data
    for email in user_emails:
        acct = Account.objects.values(*ACCOUNT_FIELDS).get(email=email)

        # Skip testers
        if acct.get("is_tester"):
            continue

        # Don't include those who signed up after the contest ended
        if contest and acct["created"] > localize(contest.end):
            continue

        dw_contest = daily_walks_summary_contest.get(email, {})
        iw_contest = intentional_walks_summary_contest.get(email, {})
        dw_baseline = daily_walks_summary_baseline.get(email, {})
        iw_baseline = intentional_walks_summary_baseline.get(email, {})

        summary_acct_and_walk_data_per_user[email] = _acct_to_row_data(
            acct, new_signup_emails, active_during_contest=True)

        summary_acct_and_walk_data_per_user[email].update({
            "Total Daily Walks During Baseline": dw_baseline.get("dw_count"),
            "Total Daily Walks During Contest": dw_contest.get("dw_count"),
            "Total Steps During Baseline": dw_baseline.get("dw_steps"),
            "Total Steps During Contest": dw_contest.get("dw_steps"),
            "Total Recorded Walks During Baseline": iw_baseline.get("rw_count"),
            "Total Recorded Walks During Contest": iw_contest.get("rw_count"),
            "Total Recorded Steps During Baseline": iw_baseline.get("rw_steps"),
            "Total Recorded Steps During Contest": iw_contest.get("rw_steps"),
            "Total Recorded Walk Time During Baseline": (
                                                                iw_contest.get("rw_total_walk_time").total_seconds()
                                                                - iw_contest.get("rw_pause_time")
                                                        ) / 60.0 if iw_contest else None,
            "Total Recorded Walk Time During Contest": (
                                                               iw_contest.get("rw_total_walk_time").total_seconds()
                                                               - iw_contest.get("rw_pause_time")
                                                       ) / 60.0 if iw_contest else None,
        })

    return summary_acct_and_walk_data_per_user


def _get_user_daily_step_counts(start_baseline: date, contest: Contest, user_emails: set) -> dict:
    daily_step_counts_by_user = defaultdict(dict)
    daily_walks_in_range = get_daily_walks_in_time_range(start_date=start_baseline, end_date=contest.end)

    for dw in daily_walks_in_range:
        daily_step_counts_by_user[dw.account.email][dw.date] = dw.steps

    return daily_step_counts_by_user


def user_agg_csv_view(request) -> HttpResponse:
    if not request.user.is_authenticated:
        return HttpResponse("You are not authorized to view this!")

    # GET method with param `contest_id`
    contest_id = request.GET.get("contest_id")
    # Parse params
    if contest_id is None:
        return HttpResponse("You are not authorized to view this!")

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users_agg.csv"'

    contest = Contest.objects.get(pk=contest_id)

    # Calculate baseline date
    if not hasattr(contest, "start_baseline") or contest.start_baseline is None:
        start_baseline = contest.start - timedelta(days=30)
    else:
        start_baseline = contest.start_baseline

    csv_header = _get_user_agg_csv_header(start_date=start_baseline, end_date=contest.end)
    writer = csv.DictWriter(response, fieldnames=csv_header)
    writer.writeheader()

    # Get all walk summary data
    (daily_walks_summary_contest,
     intentional_walks_summary_contest,
     daily_walks_summary_baseline,
     intentional_walks_summary_baseline) = get_contest_walks(contest, include_baseline=True)

    daily_walks_summary_contest = daily_walks_summary_contest or {}
    intentional_walks_summary_contest = intentional_walks_summary_contest or {}
    daily_walks_summary_baseline = daily_walks_summary_baseline or {}
    intentional_walks_summary_baseline = intentional_walks_summary_baseline or {}

    user_emails_with_walks = (
            daily_walks_summary_contest.keys() |
            intentional_walks_summary_contest.keys() |
            daily_walks_summary_baseline.keys() |
            intentional_walks_summary_baseline.keys()
    )

    new_signups_sans_testers = {
        a["email"]: a for a in get_new_signups(contest, include_testers=False)
    }

    csv_rows = _get_rows_for_new_signups_without_walks(contest, user_emails_with_walks, new_signups_sans_testers)

    summary_acct_and_walk_data_by_user = _get_user_summary_acct_and_walk_data(
        contest,
        user_emails_with_walks,
        new_signups_sans_testers.keys(),
        daily_walks_summary_contest,
        intentional_walks_summary_contest,
        daily_walks_summary_baseline,
        intentional_walks_summary_baseline,
    )
    daily_step_counts_by_user = _get_user_daily_step_counts(start_baseline, contest, user_emails_with_walks)

    for email in user_emails_with_walks:
        row = summary_acct_and_walk_data_by_user[email]
        row.update(daily_step_counts_by_user[email])
        csv_rows.append(row)

    writer.writerows(csv_rows)

    return response


def users_csv_view(request) -> HttpResponse:
    if request.user.is_authenticated:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users.csv"'

        csv_header = [
            "email", "name", "zip", "age", "account_created",
            "account_last_updated", "device_id", "device_registered_on",
        ]

        writer = csv.writer(response)
        writer.writerow(csv_header)

        # Retrieve all accounts
        all_accounts = Account.objects.all().order_by("created")
        for account in all_accounts:
            # Retrieve all devices
            for device in account.device_set.all().order_by("created"):
                writer.writerow([
                    account.email,
                    account.name,
                    account.zip,
                    account.age,
                    account.created,
                    account.updated,
                    device.device_id,
                    device.created
                ])

        return response
    else:
        return HttpResponse("You are not authorized to view this!")


def daily_walks_csv_view(request) -> HttpResponse:
    if request.user.is_authenticated:
        # GET method with params `start_date` and `end_date`
        start_date_str = request.GET.get("start_date")
        end_date_str = request.GET.get("end_date")
        # Parse params
        # TODO: consider date validation
        start_date = date.fromisoformat(
            start_date_str) if start_date_str else None
        end_date = date.fromisoformat(end_date_str) if end_date_str else None

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="daily_walks.csv"'

        csv_header = [
            "email", "name", "date", "steps", "distance(m)",
            "device_id", "walk_created",
        ]
        writer = csv.writer(response)
        writer.writerow(csv_header)

        # Retrieve all accounts
        all_accounts = Account.objects.all().order_by("created")
        for account in all_accounts:
            # Retrieve daily walks filtered by date range (if specified)
            q = (
                account.dailywalk_set.filter(
                    date__range=(start_date, end_date),
                )
                if start_date and end_date
                else account.dailywalk_set.all()
            )
            for daily_walk in q.order_by("created"):
                writer.writerow([
                    account.email,
                    account.name,
                    daily_walk.date,
                    daily_walk.steps,
                    daily_walk.distance,
                    daily_walk.device.device_id,
                    daily_walk.created,
                ])

        return response
    else:
        return HttpResponse("You are not authorized to view this!")


def intentional_walks_csv_view(request) -> HttpResponse:
    if request.user.is_authenticated:
        # GET method with params `start_date` and `end_date`
        start_date_str = request.GET.get("start_date")
        end_date_str = request.GET.get("end_date")
        # Parse params
        # TODO: consider date validation
        start_date = date.fromisoformat(
            start_date_str) if start_date_str else None
        end_date = date.fromisoformat(end_date_str) if end_date_str else None

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="recorded_walks.csv"'

        csv_header = [
            "email", "name", "event_id", "start_time", "end_time", "steps",
            "pause_time(mins)", "distance(m)", "device_id", "walk_created",
        ]
        writer = csv.writer(response)
        writer.writerow(csv_header)

        # Retrieve all accounts
        all_accounts = Account.objects.all().order_by("created")
        for account in all_accounts:
            # Retrieve intentional walks filtered by date range (if specified)
            q = (
                account.intentionalwalk_set.filter(
                    start__gte=localize(start_date),
                    # time comparison happens at beginning of date
                    end__lt=(localize(end_date) + timedelta(days=1)),
                )
                if start_date and end_date
                else account.intentionalwalk_set.all()
            )
            for intentional_walk in q.order_by("created"):
                writer.writerow([
                    account.email,
                    account.name,
                    intentional_walk.event_id,
                    intentional_walk.start,
                    intentional_walk.end,
                    intentional_walk.steps,
                    intentional_walk.pause_time,
                    intentional_walk.distance,
                    intentional_walk.device.device_id,
                    intentional_walk.created,
                ])

        return response
    else:
        return HttpResponse("You are not authorized to view this!")
