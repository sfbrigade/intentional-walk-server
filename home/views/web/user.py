import json
import itertools
from django.views import View, generic

from home.models import Account, Contest

# Hacky fix to ensure distance is in miles
def m_to_mi(value):
    return value * 0.000621371

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

        # If there is no contest id passed in or if invalid, select all users
        if contest_id:
            # Get the contest associated with this id
            contest = Contest.objects.get(contest_id=contest_id)
            date_range_start = contest.start
            date_range_end = contest.end
            context["current_contest"] = contest
        else:
            date_range_start = None
            date_range_end = None

        accounts = Account.objects.all()
        context["user_stats_list"] = []
        for account in accounts:
            user_stats = {}
            user_stats["account"] = account
            # Get all daily walk data
            # Filter based on date range if it exists
            if date_range_start and date_range_end:
                daily_walks = account.dailywalk_set.all().filter(date__range=(date_range_start, date_range_end))
                intentional_walks = account.intentionalwalk_set.all().filter(
                    created__range=(date_range_start, date_range_end)
                )
            else:
                daily_walks = account.dailywalk_set.all()
                intentional_walks = account.intentionalwalk_set.all()

            user_stats["dw_steps"] = 0
            user_stats["dw_distance"] = 0
            user_stats["num_dws"] = len(daily_walks)
            for dw in daily_walks:
                user_stats["dw_steps"] += dw.steps
                user_stats["dw_distance"] += m_to_mi(dw.distance)

            # Get all recorded walk data
            user_stats["rw_steps"] = 0
            user_stats["rw_distance"] = 0
            user_stats["rw_time"] = 0
            user_stats["rw_speeds"] = []
            user_stats["num_rws"] = len(intentional_walks)
            for iw in intentional_walks:
                user_stats["rw_steps"] += iw.steps
                user_stats["rw_distance"] += m_to_mi(iw.distance)
                user_stats["rw_time"] += iw.walk_time / 60
                user_stats["rw_speeds"].append(iw.speed_mph)
            user_stats["rw_avg_speed"] = (
                sum(user_stats["rw_speeds"]) / len(user_stats["rw_speeds"]) if user_stats["rw_speeds"] else 0
            )

            context["user_stats_list"].append(user_stats)

        context["contests"] = Contest.objects.all()

        return context
