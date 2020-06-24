import json
import datetime
import itertools
from collections import Counter
from django.views import View, generic

from home.models import Account, Device, IntentionalWalk, DailyWalk

# Date range for data aggregation
START_DATE = datetime.date(2020, 4, 1)
END_DATE = datetime.datetime.today().date()


# Home page view
class HomeView(generic.TemplateView):
    template_name = "home/home.html"

    # Augment context data to
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)

        # Get aggregate stats for all users
        all_accounts = Account.objects.all().order_by("created")

        # Save the total number of users
        context["accounts"] = all_accounts.values()

        # Get signups per day
        signup_dist = {
            date: len(list(group))
            for date, group in itertools.groupby(all_accounts.values(), key=lambda x: x["created"].date())
        }

        # Fill the gaps cos google charts is annoying af
        current_date = START_DATE
        delta = datetime.timedelta(days=1)
        context["daily_signups"] = []
        # Iterate over the entire date range
        while current_date <= END_DATE:
            context["daily_signups"].append([current_date, signup_dist.get(current_date, 0)])
            current_date += delta
        # Get cumulative distribution
        context["cumu_signups"] = []
        total = 0
        for date, count in context["daily_signups"]:
            total += count
            context["cumu_signups"].append([date, total])

        # Save the total number of daily walks over time
        daily_walks = DailyWalk.objects.all().values()
        # Get walks per day
        step_dist = {
            date: sum([walk["steps"] for walk in group])
            for date, group in itertools.groupby(daily_walks.values(), key=lambda x: x["date"])
        }
        # Fill the gaps cos google charts is annoying af
        current_date = START_DATE
        delta = datetime.timedelta(days=1)
        context["daily_steps"] = []
        # Iterate over the entire date range
        while current_date <= END_DATE:
            context["daily_steps"].append([current_date, step_dist.get(current_date, 0)])
            current_date += delta
        context["cumu_steps"] = []
        total_steps = 0
        for date, steps in context["daily_steps"]:
            total_steps += steps
            context["cumu_steps"].append([date, total_steps])
        context["total_steps"] = total_steps

        # Get growth for mile
        mile_dist = {
            date: sum([walk["distance"] for walk in group])
            for date, group in itertools.groupby(daily_walks.values(), key=lambda x: x["date"])
        }
        # Fill the gaps cos google charts if annoying af
        current_date = START_DATE
        delta = datetime.timedelta(days=1)
        context["daily_miles"] = []
        # Iterate over the entire date range
        while current_date <= END_DATE:
            context["daily_miles"].append([current_date, mile_dist.get(current_date, 0)])
            current_date += delta
        context["cumu_miles"] = []
        total_miles = 0
        for date, mile in context["daily_miles"]:
            total_miles += mile
            context["cumu_miles"].append([date, total_miles])
        context["total_miles"] = total_miles

        return context
