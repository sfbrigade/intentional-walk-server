from datetime import date as date_type

from ninja import Field, Schema
from pydantic import computed_field


class DailyWalkIn(Schema):
    date: str = Field(
        description="The specific date for which the steps are recorded"
    )
    steps: int = Field(ge=0, description="Number of steps recorded")
    distance: float = Field(ge=0, description="Total distance covered")

    class Config(Schema.Config):
        extra = "forbid"


class DailyWalkInSchema(Schema):
    account_id: str = Field(
        description="Unique identifier for user's account."
    )
    daily_walks: list[DailyWalkIn] = Field(
        description="List of record daily walks: date, steps, distance."
    )

    class Config(Schema.Config):
        extra = "forbid"


class DailyWalkOut(Schema):
    date: date_type = Field(
        description="The specific date for which the steps are recorded"
    )
    steps: int = Field(ge=0, description="Number of steps recorded")
    distance: float = Field(ge=0, description="Total distance covered")


class DailyWalkOutSchema(Schema):
    daily_walks: list[DailyWalkOut] = Field(
        default=None,
        description="List of record daily walks: date, steps, distance.",
    )

    @computed_field
    @property
    def total_steps(self) -> int:
        return sum(daily_walk.steps for daily_walk in self.daily_walks)

    @computed_field
    @property
    def total_distance(self) -> float:
        return sum(daily_walk.distance for daily_walk in self.daily_walks)


class ErrorSchema(Schema):
    message: str = Field(
        description="Error message to display",
    )
