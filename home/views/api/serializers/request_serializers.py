"""
This module contains serializers that are used for parsing and validating request data.

Each serializer in this module corresponds to a specific API endpoint. The serializer's
`validate` method is responsible for validating the incoming request data and preparing
it for further processing.
"""

from rest_framework import serializers
from datetime import timedelta
from home.models import Contest
from django.db.models import (
    BooleanField,
    Count,
    ExpressionWrapper,
    F,
    Q,
    Sum,
)


class GetUsersReqSerializer(serializers.Serializer):
    contest_id = serializers.CharField(
        required=False,
        help_text="The ID of the contest to filter by."
        + "Providing this also will add additional metrics related to te contest.",
    )
    # If true, will only return tester accounts.
    is_tester = serializers.BooleanField(
        required=False, help_text="If true, will only return tester accounts."
    )
    # Choices are: age, contests, created, dailywalk, device, email, gender, gender_other, id,
    # intentionalwalk,  is_latino, is_sf_resident, is_tester, iw_count, iw_distance, iw_steps,
    # iw_time, leaderboard, name, race, race_other, sexual_orien, sexual_orien_other, updated,
    # weeklygoal, zip.
    # TODO: Can move this to the choices field tuple.
    # which will allow some tools to auto-pick up.
    order_by = serializers.CharField(
        required=False,
        help_text="The field to order the results by. Prefix with '-' to order in descending order."
        + "The secondary sort and default sort will be lexicographically, the 'name'.",
    )
    page = serializers.IntegerField(
        required=False,
        help_text="The page number to return. Defaults to 1.",
        default=1,
    )
    query = serializers.CharField(
        required=False,
        help_text="Query string to filter for containment in the name or email.",
    )

    def validate(self, data):
        """Validates and prepares the incoming request data.

        Converts the request params into FilterSet params and annotations.
        """
        contest_id = data.get("contest_id")
        is_tester = data.get("is_tester")
        order_by = data.get("order_by")
        page = data.get("page") or 1
        per_page = 25
        query = data.get("query")

        # filter and annotate based on contest_id
        filters, annotate, intentionalwalk_filter = None, None, None
        if contest_id:
            contest = Contest.objects.get(pk=contest_id)
            dailywalk_filter = Q(
                dailywalk__date__range=(contest.start, contest.end)
            )

            filters = Q(contests__contest_id=contest_id)
            annotate = {
                "is_new": ExpressionWrapper(
                    Q(
                        created__gte=contest.start_promo,
                        created__lt=contest.end + timedelta(days=1),
                    ),
                    output_field=BooleanField(),
                ),
                "dw_count": Count("dailywalk", filter=dailywalk_filter),
                "dw_steps": Sum("dailywalk__steps", filter=dailywalk_filter),
                "dw_distance": Sum(
                    "dailywalk__distance", filter=dailywalk_filter
                ),
            }
            intentionalwalk_filter = Q(
                intentionalwalk__start__gte=contest.start,
                intentionalwalk__start__lt=contest.end + timedelta(days=1),
            )
        else:
            filters = Q()
            annotate = {
                "dw_count": Count("dailywalk"),
                "dw_steps": Sum("dailywalk__steps"),
                "dw_distance": Sum("dailywalk__distance"),
            }
            intentionalwalk_filter = Q()

        intentionalwalk_annotate = {
            "iw_count": Count(
                "intentionalwalk", filter=intentionalwalk_filter
            ),
            "iw_steps": Sum(
                "intentionalwalk__steps", filter=intentionalwalk_filter
            ),
            "iw_distance": Sum(
                "intentionalwalk__distance", filter=intentionalwalk_filter
            ),
            "iw_time": Sum(
                "intentionalwalk__walk_time", filter=intentionalwalk_filter
            ),
        }

        # filter to show users vs testers
        filters &= Q(is_tester=is_tester)

        # filter by search query
        if query:
            filters &= Q(Q(name__icontains=query) | Q(email__icontains=query))

        # set ordering
        order = []
        if order_by:
            desc = order_by.startswith("-")
            field = F(order_by[1:] if desc else order_by)
            order.append(
                field.desc(nulls_last=True)
                if desc
                else field.asc(nulls_first=None)
            )
        order.append(F("name"))

        return {
            "annotate": annotate,
            "intentionalwalk_annotate": intentionalwalk_annotate,
            "contest_id": contest_id,
            "filters": filters,
            "order_by": order,
            "page": page,
            "per_page": per_page,
        }
