import io
import csv
from django.http import HttpResponse
from django.template import loader, Context

from home.models import Account, Device, DailyWalk, IntentionalWalk

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