import io
import csv
from collections import defaultdict
from datetime import date, timedelta
from django.http import HttpResponse

from home.models import Account, Contest, Device, DailyWalk, IntentionalWalk
from home.templatetags.format_helpers import m_to_mi


def yesno(value: bool) -> str:
    return "yes" if value else "no"

def user_agg_csv_view(request) -> HttpResponse:
    if request.user.is_authenticated:
        # GET method with param `contest_id`
        contest_id = request.GET.get("contest_id")
        # Parse params
        contest = None
        if contest_id:
            contest = Contest.objects.get(pk=contest_id)

        start_date = contest.start if contest else None
        end_date = contest.end if contest else None

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users_agg.csv"'

        csv_header = [
            "email", "name", "zip", "age", "account_created", 
            "new_signup", "active_during_contest",
            "num_daily_walks", "total_steps", "total_distance(miles)",
            "num_recorded_walks", "num_recorded_steps",
            "total_recorded_distance(miles)", "total_recorded_walk_time",
            "recorded_walk_average_speed(mph)",
        ]
        writer = csv.writer(response)
        writer.writerow(csv_header)

        # Retrieve daily walks filtered by date range (if specified)
        daily_walks = (
            DailyWalk.objects.filter(
                date__range=(start_date, end_date),
            )
            if start_date and end_date
            else DailyWalk.objects.all()
        ).values('account__email','steps','distance','date')

        # Retrieve intentional walks filtered by date range (if specified)
        intentional_walks = (
            IntentionalWalk.objects.filter(
                start__gte=start_date,
                # time comparison happens at beginning of date
                end__lt=(end_date + timedelta(days=1)),
            )
            if start_date and end_date
            else IntentionalWalk.objects.all()
        ).values('account__email','steps','distance','pause_time', 'start','end')

        # HACKY GROUPBY
        daily_walks_by_acc = defaultdict(list)
        for dw in daily_walks:
            daily_walks_by_acc[dw['account__email']].append(dw)
        intentional_walks_by_acc = defaultdict(list)
        for iw in intentional_walks:
            intentional_walks_by_acc[iw['account__email']].append(iw)

        accounts = Account.objects.values('email','name','age','zip', 'created')

        for account in accounts:
            user_stats = {}
            user_stats["account"] = account

            user_daily_walks = daily_walks_by_acc.get(account["email"], [])
            user_stats["dw_steps"] = 0
            user_stats["dw_distance"] = 0
            user_stats["num_dws"] = len(user_daily_walks)
            for dw in user_daily_walks:
                user_stats["dw_steps"] += dw["steps"]
                user_stats["dw_distance"] += m_to_mi(dw["distance"])

            # Get all recorded walk data
            user_intentional_walks = intentional_walks_by_acc.get(account["email"], [])
            user_stats["rw_steps"] = 0
            user_stats["rw_distance"] = 0
            user_stats["rw_time"] = 0
            user_stats["rw_speeds"] = []
            user_stats["num_rws"] = len(user_intentional_walks)
            for iw in user_intentional_walks:
                user_stats["rw_steps"] += iw["steps"]
                user_stats["rw_distance"] += m_to_mi(iw["distance"])
                walk_time = (iw["end"]-iw["start"]).total_seconds() - int(iw["pause_time"])
                user_stats["rw_time"] += walk_time / 60
                user_stats["rw_speeds"].append(m_to_mi(iw["distance"])/ (walk_time/3600))
            user_stats["rw_avg_speed"] = (
                sum(user_stats["rw_speeds"]) / len(user_stats["rw_speeds"]) if user_stats["rw_speeds"] else 0
            )

            user_stats["active_during_contest"] = user_stats["dw_steps"] > 0
            if contest is not None:
                user_stats["new_user"] = account["created"].date() >= contest.start_promo
            else: 
                user_stats["new_user"] = None

            if user_stats["new_user"] or user_stats["active_during_contest"]:
                writer.writerow([
                    account["email"],
                    account["name"],
                    account["zip"],
                    account["age"],
                    account["created"],
                    yesno(user_stats["new_user"]),
                    yesno(user_stats["active_during_contest"]),
                    user_stats["num_dws"],
                    user_stats["dw_steps"],
                    user_stats["dw_distance"],
                    user_stats["num_rws"],
                    user_stats["rw_steps"],
                    user_stats["rw_distance"],
                    user_stats["rw_time"],
                    user_stats["rw_avg_speed"]
                ])

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
                    start__gte=start_date,
                    # time comparison happens at beginning of date
                    end__lt=(end_date + timedelta(days=1)),
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
