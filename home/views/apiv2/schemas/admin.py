from datetime import date, timedelta
from typing import Dict, List, Optional

from django.db.models import (
    BooleanField,
    Count,
    ExpressionWrapper,
    F,
    Q,
    QuerySet,
    Sum,
)
from ninja import Field, FilterSchema, ModelSchema, Schema
from ninja.errors import ValidationError
from pydantic import computed_field, field_validator, model_validator
from typing_extensions import Self

from home.models import Account, Contest


class AdminMeSchema(Schema):
    id: int = Field(description="Current logged in user's id")
    username: str = Field(description="Current logged in user's username")
    first_name: str = Field(description="Current logged in user's first name")
    last_name: str = Field(description="Current logged in user's last name")
    email: str = Field(description="Current logged in user's email")


class AdminHomeSchema(Schema):
    accounts_count: int = Field(description="Total number of users")
    accounts_steps: int = Field(
        description="Total number of steps users walked"
    )
    accounts_distance: float = Field(
        description="Total distance users walked in miles"
    )


class HomeGraphFilter(Schema):
    contest_id: str = Field(
        default=None,
        description="""The ID of the contest to filter by.
            <br>This field is mutually exclusive with the date fields.
            <br>For distance and step metrics, this will restrict the records
            to the values recorded during the contest period's start and end date.
            <br>For account metrics, this will restrict the records to the accounts that participated in the contest.""",
    )
    start_date: date = Field(
        default=None,
        description="""The start date to filter the records by.
            <br><br>**Note** start_date and end_date areThese fields are mutually exclusive with the contest_id field.""",
    )
    end_date: date = Field(
        default=None,
        description="""The end date to filter the records by.
            <br><br>**Note** start_date and end_date are mutually exclusive with the contest_id field.""",
    )
    is_tester: bool = Field(
        default=False,
        description="If true, will only return records related to tester accounts.",
    )


class HomeGraphSchema(Schema):
    date: str = Field(description="Date of data point")
    count: int | str = Field(description="Count of data points")


class HomeGraphOutSchema(Schema):
    results: list[HomeGraphSchema] = Field(
        decription="List of output values used for graphs"
    )


class ContestOutSchema(Schema):
    contest_id: str = Field(
        description="The ID of the contest.",
    )
    start: date = Field(description="Start date of the contest")
    end: date = Field(description="End date of the contest")


class UsersInSchema(Schema):
    contest_id: str = Field(
        default=None,
        description="""The ID of the contest to filter by. 
            Providing this also will add additional metrics related to te contest.""",
    )
    is_tester: bool = Field(
        default=False,
        description="If true, will only return records related to tester accounts.",
    )
    order_by: str = Field(
        default=None,
        description="""The field to order the results by. Prefix with '-' to order in descending order. 
            The secondary sort and default sort will be lexicographically, the 'name'.""",
    )
    page: int = Field(
        default=1, description="The page number to return. Defaults to 1."
    )
    query: str = Field(
        default=None,
        description="Query string to filter for containment in the name or email.",
    )

    @computed_field
    @property
    def filter_dict(self) -> int:
        filters, annotate, intentionalwalk_filter = None, None, None
        if self.contest_id:
            contest = Contest.objects.get(pk=self.contest_id)
            dailywalk_filter = Q(
                dailywalk__date__range=(contest.start, contest.end)
            )

            filters = Q(contests__contest_id=self.contest_id)
            annotate = {
                "is_new": ExpressionWrapper(
                    Q(
                        created__gte=contest.start_promo,
                        created__lt=contest.end + timedelta(days=1),
                    ),
                    output_field=BooleanField(),
                ),
                "dw_count": Count("dailywalk", filter=dailywalk_filter),
                "dw_steps": Sum(
                    "dailywalk__steps", filter=dailywalk_filter, default=0
                ),
                "dw_distance": Sum(
                    "dailywalk__distance", filter=dailywalk_filter, default=0
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
                "dw_steps": Sum("dailywalk__steps", default=0),
                "dw_distance": Sum("dailywalk__distance", default=0),
            }
            intentionalwalk_filter = Q()

        intentionalwalk_annotate = {
            "iw_count": Count(
                "intentionalwalk", filter=intentionalwalk_filter
            ),
            "iw_steps": Sum(
                "intentionalwalk__steps",
                filter=intentionalwalk_filter,
                default=0,
            ),
            "iw_distance": Sum(
                "intentionalwalk__distance",
                filter=intentionalwalk_filter,
                default=0,
            ),
            "iw_time": Sum(
                "intentionalwalk__walk_time",
                filter=intentionalwalk_filter,
                default=0,
            ),
        }

        # filter to show users vs testers
        filters &= Q(is_tester=self.is_tester)

        # filter by search query
        if self.query:
            filters &= Q(
                Q(name__icontains=self.query) | Q(email__icontains=self.query)
            )

        # set ordering
        order = []
        if self.order_by:
            desc = self.order_by.startswith("-")
            field = F(self.order_by[1:] if desc else self.order_by)
            order.append(
                field.desc(nulls_last=True)
                if desc
                else field.asc(nulls_first=False)
            )
        order.append(F("name"))

        return {
            "annotate": annotate,
            "intentionalwalk_annotate": intentionalwalk_annotate,
            "contest_id": self.contest_id,
            "filters": filters,
            "order_by": order,
            "page": self.page,
            "per_page": 25,
        }

    # @property
    def update_user_dto(self, dto, iw_stats):
        dto.update(iw_stats)
        # at this point, we have enough info to determine if user is "active"
        if self.contest_id:
            dto["is_active"] = dto["dw_count"] > 0 or dto["iw_count"] > 0
        return dto


class UsersOut(ModelSchema):
    dw_count: int = Field(description="Total number of daily walk users")
    dw_steps: int = Field(
        description="Total number of steps users took on daily walks"
    )
    dw_distance: float = Field(
        description="Total distance in miles users took on daily walks"
    )
    iw_count: int = Field(
        default=None,
        description="Total number of users that took intentional walks",
    )
    iw_steps: int = Field(
        default=None,
        description="Total number of steps users took on intentional walks",
    )
    iw_distance: float = Field(
        default=None,
        description="Total distance in miles users took on daily walks",
    )
    iw_time: int = Field(
        default=None,
        description="Total amount of time users went on intentional walks",
    )
    is_new: bool = Field(
        default=None,
    )
    is_active: bool = None

    class Meta:
        model = Account
        # fields = "__all__"
        fields = ("name", "email", "age", "zip", "created")


class UsersOutSchema(Schema):
    users: List[UsersOut] = Field(default=None)


class UsersByZipInSchema(Schema):
    contest_id: str = Field(
        default=None, description="The ID of the contest to filter by."
    )
    is_tester: bool = Field(
        default=False,
        description="If true, will only return records related to tester accounts.",
    )


class UsersByZipOutSchema(Schema):
    total: dict[str, int] = Field(
        description="Total number of users in each zip code"
    )
    new: dict[str, int] = Field(
        default=None,
        description="Total number of users in each zip code from contest promo start to contest end date",
    )


class HistogramInSchema(Schema):
    field: str = Field(description="The field to group by")
    contest_id: str = Field(
        default=None,
        description="""The ID of the contest to filter by.
            <br>This field is mutually exclusive with the date fields.
            <br>For distance and step metrics, this will restrict the records
            to the values recorded during the contest period's start and end date.
            <br>For account metrics, this will restrict the records to the accounts that participated in the contest.""",
    )
    is_tester: bool = Field(
        default=False,
        description="If true, will only return records related to tester accounts.",
    )
    bin_size: int = Field(
        default=None,
        description="""The size of the bin to group the data by. Units will be the same as the field.
            <br><br>**Note** this is mutually exclusive with the bin_count and bin_custom field.""",
    )
    bin_count: int = Field(
        default=None,
        description="""The number of bins to group the data by.
            <br><br>**Note** this is mutually exclusive with the bin_size and bin_custom field.""",
    )
    bin_custom: str = Field(
        default=None,
        description="""A list of comma separated custom bin sizes in increasing order to group the data by.
            <br><br>Example: 0,18,29,44,59
            <br><br>**Note** this is mutually exclusive with the bin_size and bin_count fields.""",
    )

    # Date fields to filter by, inclusive.
    # These fields are mutually exclusive with the contest_id field.
    start_date: date = Field(
        default=None,
        description="""The start date to filter the records by.
            <br><br>**Note** start_date and end_date areThese fields are mutually exclusive with the contest_id field.""",
    )
    end_date: date = Field(
        default=None,
        description="""The end date to filter the records by.
            <br><br>**Note** start_date and end_date are mutually exclusive with the contest_id field.""",
    )

    @field_validator("bin_custom")
    def str_to_list(cls, bin_custom):
        try:
            bin_custom: List[int] = [
                int(v) for v in bin_custom.split(",") if v
            ]
        except ValueError:
            raise ValidationError(
                {"bin_custom": f"bin_custom could not be parsed: {bin_custom}"}
            )
        return bin_custom

    @model_validator(mode="after")
    def validate_bin_param(self) -> Self:
        bin_size = self.bin_size
        bin_count = self.bin_count
        bin_custom = self.bin_custom
        if sum((bool(x) for x in (bin_size, bin_count, bin_custom))) > 1:
            raise ValidationError(
                {
                    "non_field_errors": "bin_size, bin_count and bin_custom are mutually exclusive."
                }
            )
        if not bin_size and not bin_count and not bin_custom:
            raise ValidationError(
                {
                    "non_field_errors": "bin_size, bin_count, or bin_custom is required."
                }
            )
        if bin_size and bin_size <= 0:
            raise ValidationError(
                {"bin_size": "bin_size must be greater than 0."}
            )

        if bin_count and bin_count < 2:
            raise ValidationError(
                {"bin_count": "bin_count must be greater than 1."}
            )

        if bin_custom:
            increasing = all(a < b for a, b in zip(bin_custom, bin_custom[1:]))
            if not increasing:
                raise ValidationError(
                    {
                        "bin_custom": "bin_custom values must be in increasing order."
                    }
                )
            if not all([x >= 0 for x in bin_custom]):
                raise ValidationError(
                    {"bin_custom": "bin_custom values must be positive."}
                )

        return self


class Bins(Schema):
    bin_idx: int = Field(
        description="The start of the bin",
    )
    bin_start: int = Field(
        description="The end of the bin",
    )
    bin_end: int = Field(
        default=None,
        description="The end of the bin",
    )
    count: int = Field(
        description="The count in the bin",
    )


class HistogramOutSchema(Schema):
    data: List[Bins]
    bin_size: int = Field(
        default=None,
        description="""The size of the bin to group the data by. Units will be the same as the field.
            <br><br>**Note** this is mutually exclusive with the bin_count and bin_custom field.""",
    )
    bin_count: int = Field(
        default=None,
        description="""The number of bins to group the data by.
            <br><br>**Note** this is mutually exclusive with the bin_size and bin_custom field.""",
    )
    bin_custom: List[int] | None = Field(
        default=None,
        description="""A list of comma separated custom bin sizes in increasing order to group the data by. 
            <br><br>Example: 0,18,29,44,59 
            <br><br>Note this is mutually exclusive with the bin_size and bin_count fields.""",
    )
    unit: str = Field(description="The unit of measurement for the data")


class ErrorSchema(Schema):
    message: str = Field(
        description="Error message to display",
    )
