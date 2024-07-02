from datetime import date
from typing import Dict, List, Optional

from django.db.models import QuerySet
from ninja import Field, FilterSchema, Schema
from ninja.errors import ValidationError
from pydantic import field_validator, model_validator
from typing_extensions import Self


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
            <br>This field is mutually exclusive with the date fields.
            <br>For distance and step metrics, this will restrict the records
            to the values recorded during the contest period's start and end date.
            <br>For account metrics, this will restrict the records to the accounts that participated in the contest.""",
    )
    is_tester: bool = Field(
        default=False,
        description="If true, will only return records related to tester accounts.",
    )
    order_by: str = None
    page: int = None
    query: str = None


class UsersOutSchema(Schema):
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


class UsersByZipActiveInSchema(Schema):
    contest_id: str = Field(
        default=None, description="The ID of the contest to filter by."
    )
    is_tester: bool = Field(
        default=False,
        description="If true, will only return records related to tester accounts.",
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
