from datetime import datetime

from ninja import Field, Schema
from pydantic import ConfigDict, computed_field


class IntentionalWalkInBaseSchema(Schema):
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(
        max_length=250,
        description="v4 random uuid generated on the client.",
    )
    start: datetime = Field(
        description="Timestamp when the intentional walk started."
    )
    end: datetime = Field(
        descripition="Timestamp when the intentional walk ended."
    )
    steps: int = Field(ge=0, description="Number of steps recorded.")
    pause_time: float = Field(
        ge=0, description="Total time paused (in seconds)."
    )
    distance: float = Field(ge=0, description="Total distance covered.")


class IntentionalWalkInSchema(Schema):
    account_id: str = Field(
        max_length=250,
        description="Account id of the account the data is linked to",
    )
    intentional_walks: list[IntentionalWalkInBaseSchema] = Field(
        description="List of recorded intentional walks."
    )


class IntentionalWalkOutBaseSchema(Schema):
    event_id: str = Field(
        max_length=250, description="v4 random uuid generated on the client."
    )
    start: datetime = Field(
        description="Timestamp when the intentional walk started."
    )
    end: datetime = Field(
        descripition="Timestamp when the intentional walk ended."
    )
    steps: int = Field(ge=0, description="Number of steps recorded.")
    pause_time: float = Field(
        ge=0, description="Total time paused (in seconds)."
    )
    walk_time: float = Field(
        ge=0, description="Total time walked not including pause time."
    )
    distance: float = Field(ge=0, description="Total distance covered.")


class IntentionalWalkOutSchema(Schema):
    intentional_walks: list[IntentionalWalkOutBaseSchema] = Field(
        description="List of recorded intentional walks."
    )

    @computed_field
    @property
    def total_steps(self) -> int:
        return sum(
            intentional_walk.steps
            for intentional_walk in self.intentional_walks
        )

    @computed_field
    @property
    def total_walk_time(self) -> float:
        return sum(
            intentional_walk.walk_time
            for intentional_walk in self.intentional_walks
        )

    @computed_field
    @property
    def total_pause_time(self) -> float:
        return sum(
            intentional_walk.pause_time
            for intentional_walk in self.intentional_walks
        )

    @computed_field
    @property
    def total_distance(self) -> float:
        return sum(
            intentional_walk.distance
            for intentional_walk in self.intentional_walks
        )


class ErrorSchema(Schema):
    message: str = Field(
        description="Error message to display",
    )
