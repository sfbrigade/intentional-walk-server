import json
import datetime
import itertools
from collections import Counter
from django.views import View, generic
from django.db.models import Sum

from home.models import Account, Device, IntentionalWalk, DailyWalk

# Date range for data aggregation
START_DATE = datetime.date(2020, 4, 1)
END_DATE = datetime.datetime.today().date()


class IntentionalWalkWebView(generic.ListView):
    template_name = "home/iw_list.html"
    model = IntentionalWalk

    # Augment context data to
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)

        # Get aggregate stats for all users
        all_accounts = Account.objects.all().order_by("created")

        # Get recorded walks per day
        recorded_walks = IntentionalWalk.objects.all().values()
        recorded_walks_stats = {}
        for date, group in itertools.groupby(recorded_walks, key=lambda x: x["start"].date()):
            recorded_walks_stats[date] = {"count": 0, "steps": 0, "time": 0, "miles": 0}
            for obj in group:
                recorded_walks_stats[date]["count"] += 1  # Update count
                recorded_walks_stats[date]["steps"] += obj["steps"]  # Update count
                recorded_walks_stats[date]["time"] += (obj["end"] - obj["start"]).total_seconds() - obj["pause_time"]
                recorded_walks_stats[date]["miles"] += obj["distance"]  # Update count

        # Fill the gaps cos google charts if annoying af
        current_date = START_DATE
        delta = datetime.timedelta(days=1)
        context["daily_recorded_walks_stats"] = []
        # Iterate over the entire date range
        while current_date <= END_DATE:
            context["daily_recorded_walks_stats"].append(
                [current_date, recorded_walks_stats.get(current_date, {"count": 0, "steps": 0, "time": 0, "miles": 0})]
            )
            current_date += delta
        context["cumu_recorded_walks_stats"] = []
        total = {"count": 0, "steps": 0, "time": 0, "miles": 0}
        for date, stat_obj in context["daily_recorded_walks_stats"]:
            # NOTE: Counters represent 0 counts as an empty dict and wont guarantee keys existence
            total["count"] += stat_obj["count"]
            total["steps"] += stat_obj["steps"]
            total["time"] += stat_obj["time"]
            total["miles"] += stat_obj["miles"]
            context["cumu_recorded_walks_stats"].append([date, dict(total)])
        context["total_iw_stats"] = total
        context["total_iw_stats"]["time"] = int(context["total_iw_stats"]["time"] / 60)

        # Get IW users
        context["total_iw_users"] = IntentionalWalk.objects.values("account").distinct().count()
        context["total_signedup"] = len(all_accounts)
        context["percent_usage"] = (
            (context["total_iw_users"] / context["total_signedup"]) * 100 if context["total_signedup"] > 0 else 0
        )
        context["total_steps"] = DailyWalk.objects.all().aggregate(Sum("steps"))["steps__sum"]
        context["percent_steps"] = (
            (context["total_iw_stats"]["steps"] / context["total_steps"]) * 100 if context["total_steps"] > 0 else 0
        )
        context["total_distance"] = DailyWalk.objects.all().aggregate(Sum("distance"))["distance__sum"]
        context["percent_distance"] = (
            (context["total_iw_stats"]["miles"] / context["total_distance"]) * 100
            if context["total_distance"] > 0
            else 0
        )

        return context
