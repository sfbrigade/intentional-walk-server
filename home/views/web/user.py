import itertools
import json
import logging

from django.views import View, generic
from django.db.models import Sum
from home.models import Account, DailyWalk, IntentionalWalk, Contest
from collections import defaultdict
from home.templatetags.format_helpers import m_to_mi

logger = logging.getLogger(__name__)

# User list page
class UserListView(generic.ListView):
    template_name = "home/user_list.html"
    model = Account

    # Augment context data to
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)

        # Check if url has any contest parameters
        contest_id = self.request.GET.get("contest_id")

        # Default href for download button
        context["download_url"] = "/data/users_agg.csv"

        # Hacky groupby in django
        # If there is no contest id passed in or if invalid, select all users
        if contest_id:
            # Get the contest associated with this id
            contest = Contest.objects.get(contest_id=contest_id)
            daily_walks = DailyWalk.objects.filter(date__range=(contest.start, contest.end)).values('account__email','steps','distance','date')
            intentional_walks = IntentionalWalk.objects.filter(created__range=(contest.start, contest.end)).values('account__email','steps','distance','pause_time', 'start','end')
            logger.info(f"For contest id '{contest_id}':")
            logger.info(f"  daily walks: {len(daily_walks)}, intentional walks: {len(intentional_walks)}")
            context["current_contest"] = contest
            context["download_url"] += f"?contest_id={contest_id}"
        else:
            daily_walks = DailyWalk.objects.all().values('account__email','steps','distance','date')
            intentional_walks = IntentionalWalk.objects.all().values('account__email','steps','distance','pause_time', 'start','end')


        # HACKY GROUPBY
        daily_walks_by_acc = defaultdict(list)
        for dw in daily_walks:
            daily_walks_by_acc[dw['account__email']].append(dw)
        intentional_walks_by_acc = defaultdict(list)
        for iw in intentional_walks:
            intentional_walks_by_acc[iw['account__email']].append(iw)

        accounts = Account.objects.values('email','name','age','zip','is_sf_resident','created')

        context["user_stats_list"] = []
        zipcounts = defaultdict(lambda: 0)

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

            if user_stats["dw_steps"] > 0:
                context["user_stats_list"].append(user_stats)
                zipcounts[account["zip"]] += 1

        context["contests"] = Contest.objects.all()

        # This allows us to place json (string) data into the `data-json` prop of a <div />
        # (Probably not ideal but enables us to pass data to <script /> for mapping.)
        context["zipcounts"] = json.dumps(zipcounts)

        return context
