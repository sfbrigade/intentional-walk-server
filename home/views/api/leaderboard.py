# from datetime import date, timedelta
# from typing import Optional
import json


from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

# from django.db.models import Count, F, Sum
from django.core.exceptions import ObjectDoesNotExist


from home.models import (
    # Account,
    Contest,
    # DailyWalk,
    # IntentionalWalk,
    Device,
    Leaderboard,
)

# from home.utils import localize
from .utils import validate_request_json


DEVICE_FIELDS = [
    "account",
    "account_id",
    "device_id",
]
ACCOUNT_FIELDS = [
    "email",
    "name",
    "age",
    "zip",
    "is_tester",
    "created",
    "gender",
    "gender_other",
    "race",
    "race_other",
    "is_latino",
    "sexual_orien",
    "sexual_orien_other",
    "id",
    # "device",
]


# def get_daily_walk_summaries(**filters):
#     dw = (
#         DailyWalk.objects.filter(**filters)
#         .values("account__email")
#         .annotate(
#             dw_count=Count(1),
#             dw_steps=Sum("steps"),
#             dw_distance=Sum("distance"),
#         )
#         .order_by()
#     )

#     return {row["account__email"]: row for row in list(dw)}


# def get_intentional_walk_summaries(**filters):
#     iw = (
#         IntentionalWalk.objects.filter(**filters)
#         .annotate(total_walk_time=(F("end") - F("start")))
#         .values(
#             "account__email",
#         )
#         .annotate(
#             rw_count=Count(1),
#             rw_steps=Sum("steps"),
#             rw_distance=Sum("distance"),
#             rw_total_walk_time=Sum("total_walk_time"),
#             rw_pause_time=Sum("pause_time"),
#         )
#         .order_by()
#     )

#     return {row["account__email"]: row for row in list(iw)}


# def get_daily_walks_in_time_range(start_date: date, end_date: date):
#     filters = {"date__range": (start_date, end_date)}
#     dw = DailyWalk.objects.filter(**filters)
#     return dw


# def get_contest_walks(
#     contest: Optional[Contest], include_baseline: bool = False
# ):
#     assert not (
#         contest is None and include_baseline is True
#     )  # No concept of baseline without contest

#     # Initialize filters for querying contest
#     dw_contest_filters = {}
#     iw_contest_filters = {}

#     # If there is no contest id passed in or if invalid, select all walks
#     if contest:
#         # Create filters for query
#         dw_contest_filters["date__range"] = (contest.start, contest.end)
#         iw_contest_filters["start__gte"] = localize(contest.start)
#         iw_contest_filters["end__lt"] = localize(contest.end) + timedelta(
#             days=1
#         )

#     dw_contest_summaries = get_daily_walk_summaries(**dw_contest_filters)
#     iw_contest_summaries= get_intentional_walk_summaries(**iw_contest_filters)

#     if (
#         include_baseline and contest is not None
#     ):  # No concept of baseline without a contest
#         start_baseline = getattr(contest, "start_baseline", None) or (
#             contest.start - timedelta(days=30)
#         )
#         dw_baseline_filters = {
#             "date__range": (
#                 start_baseline,
#                 contest.start - timedelta(days=1),
#             )  # start and end range both inclusive
#         }
#         iw_baseline_filters = {
#             "start__gte": localize(start_baseline),  # inclusive
#             "end__lt": contest.start,  # exclusive
#         }
#         dw_baseline_summaries= get_daily_walk_summaries(**dw_baseline_filters)
#         iw_baseline_summaries = get_intentional_walk_summaries(
#             **iw_baseline_filters
#         )
#     else:
#         dw_baseline_summaries = None
#         iw_baseline_summaries = None

#     # Fetch all walks and group by user
#     return (
#         dw_contest_summaries,
#         iw_contest_summaries,
#         dw_baseline_summaries,
#         iw_baseline_summaries,
#     )


# def get_context_data(self, request, *args, **kwargs):
#     # Call the base implementation first to get a context
#     context = super().get_context_data(**kwargs)

#     # Check if url has any contest parameters
#     contest_id = self.request.GET.get("contest_id")

#     # Check if url has any contest parameters
#     include_testers = self.request.GET.get("include_testers") is not None

#     # Default href for download button
#     context["download_url"] = "/data/users_agg.csv"

#     contest = (
#         Contest.objects.get(contest_id=contest_id) if contest_id else None
#     )
#     daily_walks, intentional_walks, _, _ = get_contest_walks(contest)

#     # Prepare loading of data into context
#     user_stats_container = {}
#     context["user_stats_list"] = []

#     # If a contest is specified, include all new signups, regardless of
#     # whether they walked during the contest or not.
#     if contest is not None:
#         # Context variables
#         context["current_contest"] = contest
#         context["download_url"] += f"?contest_id={contest_id}"

#         # # Find everyone who signed up during the constest
#         # for acct in get_new_signups(contest, include_testers):
#         #     if acct["email"] not in daily_walks:
#         #         user_stats_container[acct["email"]] = dict(
#         #             new_signup=True, account=acct
#         #         )
#         #         new_signups_by_zip[acct["zip"]] += 1

#     # Add all accounts found in filtered daily walk data
#     for email, dw_row in daily_walks.items():
#         acct = Account.objects.values(*ACCOUNT_FIELDS).get(email=email)

#         # Skip testers unless include_testers
#         if not include_testers and acct.get("is_tester"):
#             continue

#         # Don't include those who signed up after the contest ended
#         if contest and acct["created"] > localize(contest.end):
#             continue

#         user_stats = user_stats_container.get(
#             email, dict(new_signup=False)
#         )
#         user_stats["account"] = acct
#         user_stats["dw_steps"] = dw_row["dw_steps"]

#         # Also add recorded walk data
#         iw_row = intentional_walks.get(email)
#         if iw_row:
#             user_stats["rw_steps"] = iw_row["rw_steps"]
#             user_stats["rw_distance"] = iw_row["rw_distance"]
#             user_stats["rw_time"] = (
#                 iw_row["rw_total_walk_time"].total_seconds()
#                 - iw_row["rw_pause_time"]
#             ) / 60  # minutes
#         user_stats["num_rws"] = iw_row["rw_count"] if iw_row else 0

#         # Put user_stats (row) back into container
#         user_stats_container[email] = user_stats

#     context["user_stats_list"] = user_stats_container.values()
#     context["contests"] = Contest.objects.all()

#     return context


#
@method_decorator(csrf_exempt, name="dispatch")
class LeaderboardListView(View):
    """View to retrieve leaderboard"""

    # model = DailyWalk
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        json_data = json.loads(request.body)

        # Validate json. If any field is missing, send back the response message
        json_status = validate_request_json(
            json_data,
            required_fields=["account_id"],
        )
        if "status" in json_status and json_status["status"] == "error":
            return JsonResponse(json_status)

        # Get the device if already registered
        try:
            device = Device.objects.get(device_id=json_data["account_id"])
        except ObjectDoesNotExist:
            return JsonResponse(
                {
                    "status": "error",
                    "message": (
                        "Unregistered device - "
                        f"{json_data['account_id']}."
                        " Please register first!"
                    ),
                }
            )
        # Json response template
        json_response = {
            "status": "success",
            "message": "Leaderboard accessed successfully",
            "payload": {
                "account_id": device.device_id,
                "leaderboard": [],
            },
        }

        # def get(self, request, *args, **kwargs):
        # user_stats_container = {}

        contest = Contest.active()

        # daily_walks, intentional_walks, _, _ = get_contest_walks(contest)

        # # get the current/next Contest
        leaderboard_list = []
        # user_steps = {}
        # for email, dw_row in daily_walks.items():
        #     acct = Account.objects.values(*ACCOUNT_FIELDS).get(email=email)
        #    # print("acct", acct)
        #     accountid = acct.get("id")
        #     dev_id = (
        #         Account.objects.values("device")
        #         .filter(id=accountid)
        #         .reverse()[0]
        #     )
        #     #print("dev_id", dev_id)
        #     dev = Device.objects.values(*DEVICE_FIELDS).filter(
        #         account_id=accountid
        #     )[0]
        #    # print("device id", dev)
        #    # print("iso d", dev["device_id"])
        #     # print("id, ",Device.objects.get("device_id"))
        #     if contest and acct["created"] > localize(contest.end):
        #         continue

        #     user_stats = user_stats_container.get(
        #         email, dict(new_signup=False)
        #     )
        #     user_stats["account"] = acct
        #     user_stats["dw_steps"] = dw_row["dw_steps"]
        #     id = acct["id"]
        #     # device = Device.objects.get(device_id = acct)
        #     # print(device)

        #     # id = device.device_id
        #     # device = Device.objects.get(device_id=json_data["account_id"])
        #     rank = -1
        #     user_steps[id] = dw_row["dw_steps"]
        #     leaderboard_list.append(
        #         {"rank":rank, "id": dev["device_id"], "steps": user_steps[id]}
        #     )
        contest = Contest.active()
        leaderboard_list = []
        leaderboard_length = 10

        # c = [(idx, item) for idx,item in enumerate(leaderboard_list, start=1)]

        def build_dict(seq, key):
            return list(
                (dict(d, rank=rank + 1)) for (rank, d) in enumerate(seq)
            )

        leaderboard = Leaderboard.objects.all()
        model_leaderboard_list = []
        for participant in leaderboard:
            leader_dict = {}
            leader_dict["id"] = participant.device.device_id
            leader_dict["steps"] = participant.steps

            model_leaderboard_list.append(leader_dict)
        # print("dict", model_leaderboard_list)

        leaderboard_list = sorted(
            model_leaderboard_list, key=lambda user: -user["steps"]
        )

        leaderboard_list = build_dict(leaderboard_list, key="steps")
        #  current_user = {}
        #  current_user_range = []

        for count, user in enumerate(leaderboard_list):
            # print("if", user["id"], json_data["account_id"])
            if (
                user["id"] in json_data["account_id"]
                and user["rank"] > leaderboard_length
            ):
                # current_user_range.append(leaderboard_list[count-1])
                # current_user_range.append(leaderboard_list[count])
                # current_user_range.append(leaderboard_list[count+1])
                current_user = user

        # cut list to 10 items, add current user
        leaderboard_list = leaderboard_list[:leaderboard_length]
        leaderboard_list.append(current_user)
        # leaderboard_list.extend(current_user_range)
        json_response["payload"]["leaderboard"] = leaderboard_list

        if contest is None:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "There are no contests",
                }
            )
        return JsonResponse(json_response)
