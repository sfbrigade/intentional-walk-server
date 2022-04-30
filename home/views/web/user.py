import itertools
import json
import logging

from collections import defaultdict
from datetime import date, timedelta
from django import template
from django.views import View, generic
from django.db.models import Count, F, Sum
from typing import Optional

from home.models import Account, DailyWalk, IntentionalWalk, Contest
from home.templatetags.format_helpers import m_to_mi
from home.utils import localize


logger = logging.getLogger(__name__)
ACCOUNT_FIELDS = ["email", "name", "age", "zip", "is_tester", "created",
                  "gender", "gender_other", "race", "race_other", "is_latino",
                  "sexual_orien", "sexual_orien_other"]

# HELPER CLASS/FUNCTIONS


def get_daily_walk_summaries(**filters):
    dw = (
        DailyWalk.objects.filter(**filters)
        .values("account__email")
        .annotate(
            dw_count=Count(1),
            dw_steps=Sum("steps"),
            dw_distance=Sum("distance"),
        )
        .order_by()
    )

    return {row["account__email"]: row for row in list(dw)}


def get_intentional_walk_summaries(**filters):
    iw = (
        IntentionalWalk.objects.filter(**filters)
        .annotate(total_walk_time=(F("end") - F("start")))
        .values(
            "account__email",
        )
        .annotate(
            rw_count=Count(1),
            rw_steps=Sum("steps"),
            rw_distance=Sum("distance"),
            rw_total_walk_time=Sum("total_walk_time"),
            rw_pause_time=Sum("pause_time"),
        )
        .order_by()
    )

    return {row["account__email"]: row for row in list(iw)}


def get_daily_walks_in_time_range(start_date: date, end_date: date):
    filters = {"date__range": (start_date, end_date)}
    dw = DailyWalk.objects.filter(**filters)
    return dw


def get_contest_walks(contest: Optional[Contest], include_baseline: bool = False):
    assert not (contest is None and include_baseline is True)  # No concept of baseline without contest

    # DailyWalk and IntentionalWalk accessors
    daily_walks = DailyWalk.objects
    intentional_walks = IntentionalWalk.objects

    # Initialize filters for querying contest
    dw_contest_filters = {}
    iw_contest_filters = {}

    # If there is no contest id passed in or if invalid, select all walks
    if contest:
        # Create filters for query
        dw_contest_filters["date__range"] = (contest.start, contest.end)
        iw_contest_filters["start__gte"] = localize(contest.start)
        iw_contest_filters["end__lt"] = localize(contest.end) + timedelta(days=1)

    dw_contest_summaries = get_daily_walk_summaries(**dw_contest_filters)
    iw_contest_summaries = get_intentional_walk_summaries(**iw_contest_filters)

    if include_baseline and contest is not None:  # No concept of baseline without a contest
        start_baseline = getattr(contest, "start_baseline", None) or (contest.start - timedelta(days=30))
        dw_baseline_filters = {
            "date__range": (start_baseline, contest.start - timedelta(days=1))  # start and end range both inclusive
        }
        iw_baseline_filters = {
            "start__gte": localize(start_baseline),  # inclusive
            "end__lt": contest.start,  # exclusive
        }
        dw_baseline_summaries = get_daily_walk_summaries(**dw_baseline_filters)
        iw_baseline_summaries = get_intentional_walk_summaries(**iw_baseline_filters)
    else:
        dw_baseline_summaries = None
        iw_baseline_summaries = None

    # Fetch all walks and group by user
    return (
        dw_contest_summaries,
        iw_contest_summaries,
        dw_baseline_summaries,
        iw_baseline_summaries
    )


def get_new_signups(contest: Contest, include_testers=False):
    accounts = Account.objects.values(*ACCOUNT_FIELDS).filter(
        created__range=(
            localize(contest.start_promo),
            localize(contest.end),
        )
    )
    return [
        a for a in accounts if include_testers or not a.get("is_tester")
    ]

########################################################################
# VIEW(S)
########################################################################
#
# User list page
#       Puts "user_stats_list" -> context
#       which is a list of rows containing user stats to be displayed
#       (see home/tempolates/home/user_list.html)
#


class UserListView(generic.ListView):
    template_name = "home/user_list.html"
    model = Account

    # Augment context data to
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)

        # Check if url has any contest parameters
        contest_id = self.request.GET.get("contest_id")

        # Check if url has any contest parameters
        include_testers = self.request.GET.get("include_testers") is not None

        # Default href for download button
        context["download_url"] = "/data/users_agg.csv"

        contest = Contest.objects.get(
            contest_id=contest_id) if contest_id else None
        daily_walks, intentional_walks, _, _ = get_contest_walks(contest)

        # Prepare loading of data into context
        user_stats_container = {}
        context["user_stats_list"] = []

        # `zipcounts` holds user counts by zip code for visualization
        active_by_zip = defaultdict(lambda: 0)
        all_users_by_zip = defaultdict(lambda: 0)
        new_signups_by_zip = defaultdict(lambda: 0)
        steps_by_zip = defaultdict(list)

        # If a contest is specified, include all new signups, regardless of
        # whether they walked during the contest or not.
        if contest is not None:
            # Context variables
            context["current_contest"] = contest
            context["download_url"] += f"?contest_id={contest_id}"

            # Find everyone who signed up during the constest
            for acct in get_new_signups(contest, include_testers):
                if acct["email"] not in daily_walks:
                    user_stats_container[acct["email"]] = dict(
                        new_signup=True, account=acct
                    )
                    new_signups_by_zip[acct["zip"]] += 1

        # Add all accounts found in filtered daily walk data
        for email, dw_row in daily_walks.items():
            acct = Account.objects.values(*ACCOUNT_FIELDS).get(
                email=email
            )

            # Skip testers unless include_testers
            if not include_testers and acct.get("is_tester"):
                continue

            # Don't include those who signed up after the contest ended
            if contest and acct["created"] > localize(contest.end):
                continue

            user_stats = user_stats_container.get(
                email, dict(new_signup=False))
            user_stats["account"] = acct
            user_stats["dw_steps"] = dw_row["dw_steps"]
            user_stats["dw_distance"] = m_to_mi(dw_row["dw_distance"])
            user_stats["num_dws"] = dw_row["dw_count"]

            # Also add recorded walk data
            iw_row = intentional_walks.get(email)
            if iw_row:
                user_stats["rw_steps"] = iw_row["rw_steps"]
                user_stats["rw_distance"] = iw_row["rw_distance"]
                user_stats["rw_time"] = (
                    iw_row["rw_total_walk_time"].total_seconds()
                    - iw_row["rw_pause_time"]
                ) / 60  # minutes
            user_stats["num_rws"] = iw_row["rw_count"] if iw_row else 0

            # Put user_stats (row) back into container
            user_stats_container[email] = user_stats

            # Map stats
            zipcode = acct["zip"]
            active_by_zip[zipcode] += 1
            steps_list = steps_by_zip[zipcode]
            steps_list.append(dw_row["dw_steps"])

        for user in user_stats_container.values():
            all_users_by_zip[user["account"]["zip"]] += 1

        context["user_stats_list"] = user_stats_container.values()
        context["contests"] = Contest.objects.all()

        # This allows us to place json (string) data into the `data-json` prop of a <div />
        # (Probably not ideal but enables us to pass data to <script /> for mapping.)
        context["active_by_zip"] = json.dumps(active_by_zip)
        context["all_users_by_zip"] = json.dumps(all_users_by_zip)
        context["new_signups_by_zip"] = json.dumps(new_signups_by_zip)
        context["steps_by_zip"] = json.dumps(steps_by_zip)
        context["include_testers"] = include_testers
        return context
