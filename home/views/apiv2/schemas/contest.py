from datetime import date

from ninja import Field, Schema
from pydantic import ConfigDict


class ContestSchema(Schema):
    model_config = ConfigDict(extra="forbid")

    contest_id: str = Field(description="Contest identifier")
    start_baseline: date | None = Field(
        description="Start of baseline period (prior to contest start)"
    )
    start_promo: date = Field(description="Start date of promotion")
    start: date = Field(description="Contest start date")
    end: date = Field(decription="Contest end date")


class ErrorSchema(Schema):
    message: str = Field(
        description="Error message to display",
    )
