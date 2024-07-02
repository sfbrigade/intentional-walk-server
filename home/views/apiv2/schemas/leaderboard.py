from typing import Optional

from ninja import Field, Schema
from typing_extensions import Self


class LeaderboardUserSchema(Schema):
    account_id: int = Field(
        desription="Account id of the account the data is linked to."
    )
    steps: int = Field(description="Number of steps recorded.")
    rank: int = Field(description="The rank of the user for most walks.")
    device_id: str = Field(
        default=None,
        description="Device id of the device the data is coming from.",
    )

    class Config(Schema.Config):
        extra = "forbid"


class LeaderboardSchema(Schema):
    leaderboard: list[LeaderboardUserSchema] = Field(
        description="Ranked list of users on the leaderboard."
    )


class ErrorSchema(Schema):
    message: str = Field(
        description="Error message to display",
    )
