import itertools
import json
import logging

from collections import defaultdict
from datetime import timedelta
from django.views import View, generic
from django.db.models import Count, F, Sum

from home.models import Account, DailyWalk, IntentionalWalk, Contest
from home.templatetags.format_helpers import m_to_mi
from home.utils import localize


logger = logging.getLogger(__name__)


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

        # DailyWalk and IntentionalWalk accessors
        daily_walks = DailyWalk.objects
        intentional_walks = IntentionalWalk.objects

        dw_filters = {}
        iw_filters = {}

        # If there is no contest id passed in or if invalid, select all walks
        if contest_id:
            # Get the contest associated with this id
            contest = Contest.objects.get(contest_id=contest_id)

            # Context variables
            context["current_contest"] = contest
            context["download_url"] += f"?contest_id={contest_id}"

            # Create filters for query
            dw_filters["date__range"] = (contest.start, contest.end)
            iw_filters["created__range"] = (
                localize(contest.start),
                localize(contest.end) + timedelta(days=1),
            )

        # DailyWalk.objects.filter(date__range=(c.start, c.end)) \
        # .values('account__email') \
        # .annotate(dw_steps=Sum('steps'), dw_distance=Sum('distance'), dw_count=Count("id")) \
        # .order_by()
        daily_walks = get_daily_walk_summaries(**dw_filters)
        intentional_walks = get_intentional_walk_summaries(**iw_filters)

        logger.info(f"For contest id '{contest_id}':")
        logger.info(
            f"  daily walks: {len(daily_walks)}, intentional walks: {len(intentional_walks)}"
        )

        user_stats_container = {}
        context["user_stats_list"] = []
        zipcounts = defaultdict(lambda: 0)

        # If a contest is specified, include all new signups, regardless of
        # whether they walked during the contest or not.
        if contest is not None:
            for acct in Account.objects.values(
                "email", "name", "age", "zip", "created"
            ).filter(
                created__range=(
                    localize(contest.start_promo),
                    localize(contest.end) + timedelta(days=1),
                )
            ):
                user_stats_container[acct["email"]] = dict(
                    new_signup="Yes", account=acct
                )

        # Add all accounts found in filtered daily walk data
        for email, dw_row in daily_walks.items():
            acct = Account.objects.values("email", "name", "age", "zip", "created").get(
                email=email
            )

            user_stats = user_stats_container.get(email, dict(new_signup="No"))
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
            zipcounts[acct["zip"]] += 1

        context["user_stats_list"] = user_stats_container.values()
        context["contests"] = Contest.objects.all()

        # This allows us to place json (string) data into the `data-json` prop of a <div />
        # (Probably not ideal but enables us to pass data to <script /> for mapping.)
        context["zipcounts"] = json.dumps(zipcounts)

        return context
