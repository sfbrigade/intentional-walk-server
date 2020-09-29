import json
import itertools
from django.views import View, generic
from django.db.models import Sum
from home.models import Account, DailyWalk, IntentionalWalk, Contest
from collections import defaultdict
from home.templatetags.format_helpers import m_to_mi

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

        # Hacky groupby in django
        # If there is no contest id passed in or if invalid, select all users
        if contest_id:
            # Get the contest associated with this id
            contest = Contest.objects.get(contest_id=contest_id)
            daily_walks = DailyWalk.objects.filter(date__range=(contest.start, contest.end)).values('account__email','steps','distance','date')
            intentional_walks = IntentionalWalk.objects.filter(created__range=(contest.start, contest.end)).values('account__email','steps','distance','pause_time', 'start','end')
            context["current_contest"] = contest
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

        accounts = Account.objects.values('email','name','age','zip', 'created')

        context["user_stats_list"] = []
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

            context["user_stats_list"].append(user_stats)

        context["contests"] = Contest.objects.all()

        return context