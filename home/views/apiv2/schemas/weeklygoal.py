from datetime import date
from typing import Optional

from ninja import Field, Schema
from pydantic import field_validator, model_validator
from typing_extensions import Self


class WeeklyGoalIn(Schema):
    start_of_week: str = Field(
        description="The start of the week for the goal."
    )
    steps: int = Field(ge=0, description="Step goal for the week.")
    days: int = Field(
        ge=0, description="Number of days per week to reach goal."
    )

    class Config(Schema.Config):
        extra = "forbid"


class WeeklyGoalInSchema(Schema):
    account_id: str = Field(
        description="Account id of the account the data is linked to."
    )
    weekly_goal: WeeklyGoalIn = Field(
        description="Start week, steps, and days of the weekly goal."
    )

    class Config(Schema.Config):
        extra = "forbid"


class WeeklyGoalOut(Schema):
    start_of_week: date = Field(
        description="The start of the week for the goal."
    )
    steps: int = Field(ge=0, description="Step goal for the week.")
    days: int = Field(
        ge=0, description="Number of days per week to reach goal."
    )


class WeeklyGoalOutSchema(Schema):
    account_id: int = Field(
        description="Account id of the account the data is linked to."
    )
    weekly_goal: WeeklyGoalOut = Field(
        description="Start week, steps, and days of the weekly goal."
    )


class WeeklyGoalListInSchema(Schema):
    account_id: str = Field(
        description="Account id of the account the data is linked to."
    )

    class Config(Schema.Config):
        extra = "forbid"


class WeeklyGoalOutList(Schema):
    id: int = Field(description="Unique id for the set weekly goal.")
    start_of_week: str = Field(
        description="The start of the week for the goal."
    )
    steps: int = Field(description="Step goal for the week.")
    days: int = Field(description="Number of days per week to reach goal.")
    account_id: int = Field(
        description="Account id of the account the data is linked to."
    )


class WeeklyGoalListOutSchema(Schema):
    weekly_goals: list[WeeklyGoalOutList] = Field(
        description="List of user's weekly goals."
    )


class ErrorSchema(Schema):
    message: str = Field(
        description="Error message to display",
    )
