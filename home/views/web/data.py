import io
import csv
import logging

from collections import defaultdict
from datetime import date, timedelta
from django.http import HttpResponse

from home.models import Account, Contest, Device, DailyWalk, IntentionalWalk
from home.templatetags.format_helpers import m_to_mi
from home.utils import localize
from home.views.web.user import ACCOUNT_FIELDS, get_contest_walks, get_new_signups


logger = logging.getLogger(__name__)

def yesno(value: bool) -> str:
    return "yes" if value else "no"

def user_agg_csv_view(request) -> HttpResponse:
    if request.user.is_authenticated:
        # GET method with param `contest_id`
        contest_id = request.GET.get("contest_id")
        # Parse params
        contest = Contest.objects.get(pk=contest_id) if contest_id else None
        start_date = contest.start if contest_id else None
        end_date = contest.end if contest_id else None

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users_agg.csv"'

        csv_header = [
            "email", "name", "zip", "age", "account_created",
            "is_tester", "new_signup", "active_during_contest",
            "num_daily_walks", "total_steps", "total_distance(miles)",
            "num_recorded_walks", "num_recorded_steps",
            "total_recorded_distance(miles)", "total_recorded_walk_time",
        ]
        writer = csv.DictWriter(response, fieldnames=csv_header)
        writer.writeheader()

        daily_walks, intentional_walks = get_contest_walks(contest)
        new_signups = {
            a["email"]: a for a in get_new_signups(contest, include_testers=False)
        } if contest else dict()

        for acct in new_signups.values():
            if acct["email"] not in daily_walks:
                row_data = {
                    **acct,
                    "account_created": acct["created"],
                    "new_signup": yesno(True), # new signup
                    "active_during_contest": yesno(False), # inactive
                    "num_daily_walks": 0,
                    "num_recorded_walks": 0,
                }
                row_data.pop("created")
                # row_data.pop("is_tester")
                writer.writerow(row_data)

        # Add all accounts found in filtered daily walk data
        for email, dw_row in daily_walks.items():
            acct = Account.objects.values(*ACCOUNT_FIELDS).get(
                email=email
            )

            # Skip testers
            if acct.get("is_tester"):
                continue

            # Don't include those who signed up after the contest ended
            if contest and acct["created"] > localize(contest.end):
                continue

            iw_row = intentional_walks.get(email, {})

            row_data = {
                **acct,
                "account_created": acct["created"],
                "new_signup": yesno(email in new_signups),
                "active_during_contest": yesno(True),
                "num_daily_walks": dw_row["dw_count"],
                "total_steps": dw_row["dw_steps"],
                "total_distance(miles)": m_to_mi(dw_row["dw_distance"]),
                "num_recorded_walks": iw_row.get("rw_count"),
                "num_recorded_steps": iw_row.get("rw_steps"),
                "total_recorded_distance(miles)": iw_row.get("rw_distance"),
                "total_recorded_walk_time": (
                    iw_row["rw_total_walk_time"].total_seconds()
                    - iw_row["rw_pause_time"]
                ) / 60 if iw_row else None,  # minutes
            }
            row_data.pop("created")
            writer.writerow(row_data)

        return response
    else:
        return HttpResponse("You are not authorized to view this!")


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
        start_date = date.fromisoformat(start_date_str) if start_date_str else None
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
        start_date = date.fromisoformat(start_date_str) if start_date_str else None
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
