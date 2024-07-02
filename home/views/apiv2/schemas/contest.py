from datetime import date
from typing import List, Optional

from ninja import Field, ModelSchema, Schema
from pydantic import ValidationInfo, field_validator, model_validator
from typing_extensions import Self

from home.models.contest import Contest


class ContestSchema(Schema):
    contest_id: str = Field(description="Contest identifier")
    start_baseline: date | None = Field(
        description="Start of baseline period (prior to contest start)"
    )
    start_promo: date = Field(description="Start date of promotion")
    start: date = Field(description="Contest start date")
    end: date = Field(decription="Contest end date")

    class Config(Schema.Config):
        extra = "forbid"


class ErrorSchema(Schema):
    message: str = Field(
        description="Error message to display",
    )
