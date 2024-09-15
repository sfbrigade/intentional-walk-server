from datetime import date, datetime, time
from typing import Any, Dict, List, Optional, TypedDict

from django.db import models as djmodel
from django.db.models import (
    Case,
    Count,
    ExpressionWrapper,
    F,
    IntegerField,
    Max,
    Min,
    Q,
    QuerySet,
    Value,
    When,
)
from django.db.models.functions import Floor
from django.utils.timezone import make_aware
from rest_framework import serializers

from home.models.account import Account
from home.models.contest import Contest
from home.models.dailywalk import DailyWalk
from home.models.intentionalwalk import IntentionalWalk
from home.models.leaderboard import Leaderboard


class ValidatedHistogramReq(TypedDict):
    query_set: QuerySet
    # bin_size is provided if the bins were
    # generated with equal bin sizes,
    # otherwise the bin_custom is provided.
    bin_size: Optional[int]
    bin_custom: List[int]
    bin_count: int
    unit: str


class HistogramReqSerializer(serializers.Serializer):
    """HistogramReqSerializer is a serializer for the histogram API.

    This serializer is used to validate and prepare the incoming request data
    and prepare the annotations and filters for the histogram query.
    This generates a histogram based on the bin_count or bin_size,
    or custom bin intervals.
    and the field of certain models to group by.
    """

    supported_fields = {
        Leaderboard: ["steps"],
        DailyWalk: ["steps", "distance"],
        IntentionalWalk: ["steps", "distance"],
        Account: ["age"],
    }

    field_units = {
        "steps": "steps",
        "distance": "miles",
        "age": "years",
    }

    field = serializers.CharField(
        required=True, help_text="The field to group by"
    )

    contest_id = serializers.CharField(
        required=False,
        help_text="The ID of the contest to filter by."
        + "This field is mutually exclusive with the date fields."
        + "For distance and step metrics, this will restrict the records"
        + "to the values recorded during the contest period's start and end date."
        + "For account metrics, this will restrict the records to the accounts that participated in the contest.",
    )
    is_tester = serializers.BooleanField(
        required=False,
        help_text="If true, will only return records related to tester accounts.",
    )

    bin_size = serializers.IntegerField(
        required=False,
        help_text="The size of the bin to group the data by. Units will be the same as the field."
        + "Note this is mutually exclusive with the bin_count and bin_custom field.",
    )

    bin_count = serializers.IntegerField(
        required=False,
        help_text="The number of bins to group the data by."
        + "Note this is mutually exclusive with the bin_size and bin_custom field.",
    )

    bin_custom = serializers.CharField(
        required=False,
        help_text="A list of comma separated custom bin sizes in increasing order to group the data by."
        + "Example: 0,18,29,44,59"
        + "Note this is mutually exclusive with the bin_size and bin_count fields.",
    )

    # Date fields to filter by, inclusive.
    # These fields are mutually exclusive with the contest_id field.
    start_date = serializers.DateField(
        required=False, help_text="The start date to filter the records by."
    )
    end_date = serializers.DateField(
        required=False, help_text="The end date to filter the records by."
    )

    def __init__(self, *args, model=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.model: djmodel.Model = model
        self.__unit: str = None

    def validate(self, data: Dict[str, Any]) -> ValidatedHistogramReq:
        """Validates and prepares the incoming request data.

        Converts the request params into FilterSet params and annotations.
        """
        model = self.model
        if not model:
            raise serializers.ValidationError(
                {"non_field_errors": "Model is required."}
            )

        bin_size: Optional[int] = data.get("bin_size")
        bin_count: Optional[int] = data.get("bin_count")
        bin_custom_str: Optional[str] = data.get("bin_custom", "")
        bin_custom = []
        try:
            bin_custom: List[int] = [
                int(v) for v in bin_custom_str.split(",") if v
            ]
        except ValueError:
            raise serializers.ValidationError(
                {
                    "bin_custom": f"bin_custom could not be parsed: {bin_custom_str}"
                }
            )
        field: str = data.get("field")
        contest_id: Optional[int] = data.get("contest_id")
        is_tester: Optional[bool] = data.get("is_tester")
        start_date: Optional[date] = data.get("start_date")
        end_date: Optional[date] = data.get("end_date")

        if sum((bool(x) for x in (bin_size, bin_count, bin_custom))) > 1:
            raise serializers.ValidationError(
                {
                    "non_field_errors": "bin_size, bin_count and bin_custom are mutually exclusive."
                }
            )

        if not bin_size and not bin_count and not bin_custom:
            raise serializers.ValidationError(
                {
                    "non_field_errors": "bin_size, bin_count, or bin_custom is required."
                }
            )

        if bin_size and bin_size <= 0:
            raise serializers.ValidationError(
                {"bin_size": "bin_size must be greater than 0."}
            )

        if bin_count and bin_count < 2:
            raise serializers.ValidationError(
                {"bin_count": "bin_count must be greater than 1."}
            )

        if bin_custom:
            increasing = all(a < b for a, b in zip(bin_custom, bin_custom[1:]))
            if not increasing:
                raise serializers.ValidationError(
                    {
                        "bin_custom": "bin_custom values must be in increasing order."
                    }
                )
            if not all([x >= 0 for x in bin_custom]):
                raise serializers.ValidationError(
                    {"bin_custom": "bin_custom values must be positive."}
                )

        valid_fields = self.supported_fields.get(model, [])
        if field not in valid_fields:
            raise serializers.ValidationError(
                {
                    "non_field_errors": f"{field} is not supported for {model}. Please use one of {valid_fields}."
                }
            )

        self.__unit = self.field_units.get(field)

        if contest_id and (start_date or end_date):
            raise serializers.ValidationError(
                {
                    "non_field_errors": "contest_id and start_date/end_date are mutually exclusive."
                }
            )

        contest = None
        if contest_id:
            try:
                contest = Contest.objects.get(contest_id=contest_id)
            except Contest.DoesNotExist:
                raise serializers.ValidationError(
                    {
                        "contest_id": f"Contest with id {contest_id} does not exist."
                    }
                )

        return self.create_bin_query(
            model=model,
            field=field,
            is_tester=is_tester,
            contest=contest,
            start_date=start_date,
            end_date=end_date,
            bin_count=bin_count,
            bin_size=bin_size,
            bin_custom=bin_custom,
        )

    @property
    def unit(self):
        return self.__unit

    def create_bin_query(
        self,
        model: djmodel.Model,
        field: str,
        is_tester: bool,
        contest: Contest,
        start_date: str,
        end_date: str,
        bin_count: int,
        bin_size: int,
        bin_custom: List[int],
    ) -> ValidatedHistogramReq:
        """Handle bin_count generates a histogram based on the bin_count."""
        date_filter: Q = self.get_date_filter(
            model=model,
            start_date=start_date,
            end_date=end_date,
            contest=contest,
            is_tester=is_tester,
        )

        range = model.objects.filter(date_filter).aggregate(
            max_value=Max(field),
            min_value=Min(field),
        )

        upper, lower = range.get("max_value"), range.get("min_value")
        if not upper or not lower:
            # no data was found in the range.
            return {
                "query_set": model.objects.none(),
                "bin_count": bin_count,
                "bin_custom": bin_custom,
                "bin_size": bin_size,
                "unit": self.unit,
            }

        if bin_count:
            # Using an offset because dividing by N equal parts
            # will result in N+1 bins.
            # Ex: Data ranging from 0 to 11 and divide it into two bins.
            # 11 // 2 = 5, results in 3 bins: 0-5, 5-10, 10-15 to capture the 11.
            offset = 1
            bin_size = (upper - 0) // (bin_count - offset)

            # Prevent division by zero when the
            # range is less than the bin_count itself.
            # We'll just drop everything into one bin.
            bin_size = max(bin_size, 1)
        elif bin_size:
            # Using a lower bound is an optimization
            # to reduce the search space for the query
            # for performant queries on larger or sparse datasets.
            bin_count = (upper - lower) // bin_size

        if bin_custom:
            # For custom bins, we'll create a case statement.
            cases = [
                When(
                    Q(
                        **{
                            f"{field}__gte": bin_start,
                            f"{field}__lt": bin_end,
                        }
                    ),
                    then=Value(bin_start),
                )
                for bin_start, bin_end in zip(bin_custom, bin_custom[1:])
            ]

            # SQL equivalent:
            # SELECT
            #     CASE
            #         WHEN <field> >= <bin_start> AND <field> < <bin_end> THEN <bin_start>
            #         ...
            #         WHEN <field> >= <last_bin> AND <field> < <upper> THEN <last_bin>
            #     END AS bin_start,
            #     END AS bin_start,
            #     COUNT(*) AS count
            # FROM <table_name>
            # JOIN <related_table> ON <related_table>.id = <table_name>.<related_table>_id # (if necessary)
            # WHERE <date_filter>
            # GROUP BY bin_start
            # ORDER BY bin_start
            last_bin = Value(bin_custom[-1])
            query_set = (
                model.objects.filter(date_filter)
                .annotate(
                    bin_start=Case(
                        *cases, default=last_bin, output_field=IntegerField()
                    ),
                )
                .values("bin_start")
                .annotate(count=Count("*"))
                .order_by("bin_start")
            )

            idx_lookup = {
                bin_start: idx for idx, bin_start in enumerate(bin_custom)
            }

            def get_bin_end(bin_start):
                idx_of_end = idx_lookup[bin_start] + 1
                if idx_of_end >= len(bin_custom):
                    return upper
                return bin_custom[idx_of_end]

            def get_bin_idx(bin_start):
                return idx_lookup[bin_start]

            query_set = (
                {
                    "bin_start": bin["bin_start"],
                    "bin_end": get_bin_end(bin["bin_start"]),
                    "bin_idx": get_bin_idx(bin["bin_start"]),
                    "count": bin["count"],
                }
                for bin in query_set
            )

            return {
                "query_set": query_set,
                "bin_count": len(bin_custom),
                "bin_custom": bin_custom,
                "unit": self.unit,
            }

        # For equal bins, we'll use the bin_size to generate the bins.

        #  SQL equivalent:
        #  SELECT
        #     FLOOR(<field> / <bin_size>) AS bin_idx,
        #     FLOOR(<field> / <bin_size>) * <bin_size> AS bin_start,
        #     FLOOR(<field> / <bin_size>) * <bin_size> + <bin_size> AS bin_end,
        #     COUNT(*) AS count,
        #  FROM <table_name>
        #  JOIN <related_table> ON <related_table>.id = <table_name>.<related_table>_id # (if necessary)
        #  WHERE <date_filter>
        #  GROUP BY bin
        #  ORDER BY bin
        query_set = (
            model.objects.filter(date_filter)
            .annotate(
                bin_idx=ExpressionWrapper(
                    Floor(F(field) / bin_size), output_field=IntegerField()
                ),
                bin_start=ExpressionWrapper(
                    Floor(F(field) / bin_size) * bin_size,
                    output_field=IntegerField(),
                ),
                bin_end=ExpressionWrapper(
                    Floor(F(field) / bin_size) * bin_size + bin_size,
                    output_field=IntegerField(),
                ),
            )
            .values("bin_idx", "bin_start", "bin_end")
            .annotate(count=Count("*"))
            .order_by("bin_idx")
        )

        return {
            "query_set": query_set,
            "bin_size": bin_size,
            "bin_count": bin_count,
            "unit": self.unit,
        }

    def get_date_filter(
        self,
        model: djmodel.Model,
        contest: Optional[Contest],
        start_date: Optional[date],
        end_date: Optional[date],
        is_tester: Optional[bool],
    ) -> Q:
        """Generates the correct filters for the given model.

        This is needed since the columns for dates are inconsistent across models,
        and different depending on relationships.
        """
        kwargs = {}
        if model is Leaderboard:
            if not contest:
                raise serializers.ValidationError(
                    {
                        "contest_id": "contest_id is required for Leaderboard model."
                    }
                )
            if start_date or end_date:
                raise serializers.ValidationError(
                    {
                        "non_field_errors": "start_date and end_date is not supported for the Leaderboard model."
                    }
                )

            kwargs = {
                # This looks wrong, but yes - the `contest` model *actually*
                # does stutter;
                # It is home_contest.contest_id.
                "contest__contest_id": contest.contest_id if contest else None,
                "account__is_tester": is_tester,
            }
        elif model is Account:
            # NOTE:
            # For accounts, the "contest_id" and
            # "start_date" and "end_date" will refer
            # not to the account's creation date,
            # but their participation in any walk during that contest period
            # OR the date range.

            if contest:
                # Attach time and timezone to the dates,
                # because in the database, the dates are stored as
                # date objects with no time and timezone.
                # We'll use the beginning of the start_date day,
                # and the end of the end_date day to capture all records
                start_date = make_aware(
                    datetime.combine(
                        contest.start_baseline or contest.start, time.min
                    )
                )
                end_date = make_aware(datetime.combine(contest.end, time.max))

            # SQL equivalent:
            # SELECT * FROM account WHERE id IN (
            #     SELECT account_id FROM intentional_walk
            #     WHERE start_date BETWEEN <contest.start_date> AND <contest.end_date>
            #     AND end_date BETWEEN <contest.start_date> AND <contest.end_date>
            #     UNION
            #     SELECT account_id FROM daily_walk
            #     WHERE date BETWEEN contest.start_date AND contest.end_date
            #     AND end_date BETWEEN contest.start_date AND contest.end_date
            # )
            iw_kwargs = {
                k: v
                for k, v in {
                    "start__lte": end_date,
                    "start__gte": start_date,
                    "end__lte": end_date,
                    "end__gte": start_date,
                }.items()
                if v is not None
            }
            dw_kwargs = {
                k: v
                for k, v in {
                    "date__lte": end_date,
                    "date__gte": start_date,
                }.items()
                if v is not None
            }

            kwargs = {"is_tester": is_tester}
            if iw_kwargs or dw_kwargs:
                account_walkers = (
                    IntentionalWalk.objects.filter(**iw_kwargs)
                    .values("account_id")
                    .distinct()
                    .union(
                        DailyWalk.objects.filter(**dw_kwargs)
                        .values("account_id")
                        .distinct()
                    )
                )
                kwargs["id__in"] = account_walkers
        elif model is DailyWalk:
            kwargs = {
                "date__lte": end_date,
                "date__gte": start_date,
                "account__is_tester": is_tester,
            }
        elif model is IntentionalWalk:
            kwargs = {
                "start__lte": end_date,
                "start__gte": start_date,
                "end__lte": end_date,
                "end__gte": start_date,
                "account__is_tester": is_tester,
            }
        else:
            raise serializers.ValidationError(
                {"non_field_errors": f"{model} is not yet supported."}
            )
        # Remove None values from the kwargs,
        # as they indicate optional fields that were not provided.
        return Q(**{k: v for k, v in kwargs.items() if v is not None})
