import itertools
from datetime import date, datetime, time
from typing import List, Optional, TypedDict

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
from ninja.errors import ValidationError

from home.models import (
    Account,
    Contest,
    DailyWalk,
    IntentionalWalk,
    Leaderboard,
)


class ValidatedHistogramReq(TypedDict):
    query_set: QuerySet
    # bin_size is provided if the bins were
    # generated with equal bin sizes,
    # otherwise the bin_custom is provided.
    bin_size: Optional[int]
    bin_custom: List[int]
    bin_count: int
    unit: str


class Histogram:
    # TODO: Implement a ResponseSerializer
    # to handle serialization of the response
    # (with filling of the bins)
    # to either JSON or CSV format.
    model_name: str = None
    supported_models = {
        "users": Account,
        "dailywalk": DailyWalk,
        "intentionalwalk": IntentionalWalk,
        "leaderboard": Leaderboard,
    }

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

    def __init__(self, model):
        self.model: djmodel.Model = model
        self.__unit: str = None

    @property
    def unit(self):
        return self.__unit

    def set_unit(self, unit):
        self.__unit = unit

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
                raise ValidationError(
                    {
                        "contest_id": "contest_id is required for Leaderboard model."
                    }
                )
            if start_date or end_date:
                raise ValidationError(
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
            raise ValidationError(
                {"non_field_errors": f"{model} is not yet supported."}
            )
        # Remove None values from the kwargs,
        # as they indicate optional fields that were not provided.
        return Q(**{k: v for k, v in kwargs.items() if v is not None})

    def fill_missing_bin_idx(
        self,
        query_set,
        bin_size: int = None,
        bin_custom: list = None,
        total_bin_ct: int = 0,
    ):
        """Fill in missing bin intervals lazily.

            This is because the histogram is generated from a query set that may not have
            found data in certain bins.

            For example, if the bins were [0, 18, 20, 33, 50, 70],
            which creates bins from 0-17, 18-20, 20-33, 33-50, 50-70.

            There may be no users in in the 18-20 range, and no users in the 51 and 70.
            In other words, missing on bin_idx = 1 and bin_idx = 4.
            The query would not return any groupings for the [18, 20], or [50, 70]
            This function will fill in those missing bins with a count of 0.
        #"""

        def create_filler(cursor, bin_size, bin_custom):
            res = {}
            # bin_start and bin_end are inclusive.
            if bin_custom:
                res["bin_start"] = bin_custom[cursor]
                if cursor + 1 < len(bin_custom):
                    res["bin_end"] = bin_custom[cursor + 1]
            else:
                res["bin_start"] = cursor * bin_size
                res["bin_end"] = (cursor + 1) * bin_size
            # Done down here to maintain stable order of keys.
            res["count"] = 0
            res["bin_idx"] = cursor
            return res

        bin_idx_counter = itertools.count()
        cursor = 0
        for bin in query_set:
            cursor = next(bin_idx_counter)
            curr_idx = bin["bin_idx"]
            while curr_idx > cursor:
                yield create_filler(
                    cursor=cursor, bin_size=bin_size, bin_custom=bin_custom
                )
                cursor = next(bin_idx_counter)
            yield bin

        cursor = next(bin_idx_counter)
        # Fill in the rest of the bins with 0 count,
        # until we reach the total expected count of bins.
        while cursor and cursor < total_bin_ct:
            yield create_filler(
                cursor=cursor, bin_size=bin_size, bin_custom=bin_custom
            )
            cursor = next(bin_idx_counter)
