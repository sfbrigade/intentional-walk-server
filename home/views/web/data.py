import io
import csv
from collections import defaultdict
from django.http import HttpResponse
from django.template import loader, Context

from home.models import Account, Device, DailyWalk, IntentionalWalk
from home.templatetags.format_helpers import m_to_mi


def user_agg_csv_view(request):
    if request.user.is_authenticated:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users_agg.csv"'

        csv_data = list()
        csv_data.append(["email", "name", "zip", "age", "account_created",
                         "num_daily_walks", "total_steps", "total_distance(miles)",
                         "num_recorded_walks", "num_recorded_steps", "total_recorded_distance(miles)",
                         "total_recorded_walk_time", "recorded_walk_average_speed(mph)"])

        daily_walks = DailyWalk.objects.all().values('account__email','steps','distance','date')
        intentional_walks = IntentionalWalk.objects.all().values('account__email','steps','distance','pause_time', 'start','end')

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

            csv_data.append([
                account["email"],
                account["name"],
                account["zip"],
                account["age"],
                account["created"],
                user_stats["num_dws"],
                user_stats["dw_steps"],
                user_stats["dw_distance"],
                user_stats["num_rws"],
                user_stats["rw_steps"],
                user_stats["rw_distance"],
                user_stats["rw_time"],
                user_stats["rw_avg_speed"]
            ])

        t = loader.get_template('home/user_agg_csv.txt')
        c = {'data': csv_data}
        response.write(t.render(c))
        return response
    else:
        return HttpResponse("You are not authorized to view this!")


def users_csv_view(request):
    if request.user.is_authenticated:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users.csv"'

        csv_data = list()
        csv_data.append(["email", "name", "zip",
                         "age", "account_created",
                         "account_last_updated",
                         "device_id", "device_registered_on"])

        all_accounts = Account.objects.all().order_by("created")
        for account in all_accounts:
            for device in account.device_set.all().order_by("created"):
                csv_data.append([
                    account.email,
                    account.name,
                    account.zip,
                    account.age,
                    account.created,
                    account.updated,
                    device.device_id,
                    device.created
                ])

        t = loader.get_template('home/users_csv.txt')
        c = {'data': csv_data}
        response.write(t.render(c))
        return response
    else:
        return HttpResponse("You are not authorized to view this!")


def daily_walks_csv_view(request):
    if request.user.is_authenticated:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="dailywalks.csv"'

        csv_data = list()
        csv_data.append(["email", "name", "date",
                         "steps", "distance(m)",
                         "device_id", "walk_created"])

        all_accounts = Account.objects.all().order_by("created")
        for account in all_accounts:
            for daily_walk in account.dailywalk_set.all().order_by("created"):
                csv_data.append([
                    account.email,
                    account.name,
                    daily_walk.date,
                    daily_walk.steps,
                    daily_walk.distance,
                    daily_walk.device.device_id,
                    daily_walk.created,
                ])

        t = loader.get_template('home/dailywalks_csv.txt')
        c = {'data': csv_data}
        response.write(t.render(c))
        return response
    else:
        return HttpResponse("You are not authorized to view this!")


def intentional_walks_csv_view(request):
    if request.user.is_authenticated:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="recorded_walks.csv"'

        csv_data = list()
        csv_data.append(["email", "name", "event_id",
                         "start_time", "end_time", "steps", "pause_time(mins)", "distance(m)",
                         "device_id", "walk_created"])

        all_accounts = Account.objects.all().order_by("created")
        for account in all_accounts:
            for intentional_walk in account.intentionalwalk_set.all().order_by("created"):
                csv_data.append([
                    account.email,
                    account.name,
                    intentional_walk.event_id,
                    intentional_walk.start,
                    intentional_walk.end,
                    intentional_walk.steps,
                    intentional_walk.pause_time,
                    intentional_walk.distance,
                    intentional_walk.device.device_id,
                    intentional_walk.created
                ])

        t = loader.get_template('home/intentionalwalks_csv.txt')
        c = {'data': csv_data}
        response.write(t.render(c))
        return response
    else:
        return HttpResponse("You are not authorized to view this!")

