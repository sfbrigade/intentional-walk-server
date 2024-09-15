from typing import List

from ninja import Field, Schema
from pydantic import ConfigDict, field_validator, model_validator
from typing_extensions import Self

from home.models.account import (
    SAN_FRANCISCO_ZIP_CODES,
    GenderLabels,
    IsLatinoLabels,
    RaceLabels,
    SexualOrientationLabels,
)


class AccountSchema(Schema):
    model_config = ConfigDict(extra="forbid")

    account_id: str = Field(description="Account id of the user's account")
    name: str = Field(min_length=1, max_length=250, description="User's name")
    email: str = Field(decription="Email which uniquely identifies an account")
    zip: str = Field(min_length=5, max_length=25, decription="User's zip code")
    age: int = Field(ge=1, le=200, description="User's age")
    is_latino: IsLatinoLabels | None = Field(
        default=None,
        description="""Is the user of Latin descent?
                    <br><br>Choices:
                    <br>YE = Yes
                    <br>NO = No
                    <br>DA = Decline to answer""",
    )
    race: List[RaceLabels] | None = Field(
        default=None,
        description="""User's race.
                        <br><br>Choices:
                        <br>NA = American Indian or Alaska Native
                        <br>BL = Black
                        <br>AS = Asian
                        <br>PI = Native Hawaiian or other Pacific Islander
                        <br>WH = White
                        <br>OT = Other
                        <br>DA = Decline to answer""",
    )
    race_other: str | None = Field(
        default=None,
        max_length=75,
        description="Free-form text field for 'race' value 'OT'",
    )
    gender: GenderLabels | None = Field(
        default=None,
        description="""User's self-identified gender identity.
                    <br><br>Choices:
                    <br>CF = Female
                    <br>CM = Male
                    <br>TF = Trans Female
                    <br>TM = Trans Male
                    <br>NB = Non-binary
                    <br>OT = Other
                    <br>DA = Decline to answer
                """,
    )
    gender_other: str | None = Field(
        default=None,
        max_length=75,
        description="Free-form text field for 'gender' value 'OT'",
    )
    sexual_orien: SexualOrientationLabels | None = Field(
        default=None,
        description="""Self-identified sexual orientation of user.
                    <br><br>Choices:
                    <br>BS = Bisexual
                    <br>SG = SameGenderLoving
                    <br>US = Unsure
                    <br>HS = Heterosexual
                    <br>OT = Other
                    <br>DA = Decline to answer""",
    )
    sexual_orien_other: str | None = Field(
        default=None,
        max_length=75,
        description="Free-form text field for 'sexual_orien' value 'OT'",
    )

    # Check for valid zip code
    @field_validator("zip")
    def check_zip(cls, zipcode) -> str:
        if zipcode not in SAN_FRANCISCO_ZIP_CODES:
            raise ValueError("Invalid zip code")
        return zipcode

    # Check for valid race
    @model_validator(mode="after")
    def validate_race(self) -> Self:
        race_other = self.race_other
        race = self.race
        if race:
            race = set(race)
            diff = race - set(RaceLabels.__members__)
            if diff:
                raise ValueError(f"Invalid race selection '{diff}'")
            self.race = list(race)
            if "OT" in race and not race_other:
                raise ValueError("Must specify 'other' race")
            elif "OT" not in race and race_other:
                raise ValueError(
                    "'race_other' should not be specified without race 'OT'"
                )
        elif race_other:
            raise ValueError(
                "'race_other' should not be specified without 'race'"
            )
        return self

    # Check for valid gender
    @model_validator(mode="after")
    def validate_gender(self) -> Self:
        gender = self.gender
        gender_other = self.gender_other
        if gender is not None:
            if gender == "OT":
                if not gender_other:
                    raise ValueError("Must specify 'other' gender")
            elif gender_other:
                raise ValueError(
                    "'gender_other' should not be specified without 'OT'"
                )
        elif gender_other:
            raise ValueError(
                "'gender_other' should not be specified without 'gender'"
            )
        return self

    # Check for valid sex_orien
    @model_validator(mode="after")
    def validate_sex_orien(self) -> Self:
        sexual_orien = self.sexual_orien
        sexual_orien_other = self.sexual_orien_other
        if sexual_orien is not None:
            if sexual_orien == "OT":
                if not sexual_orien_other:
                    raise ValueError("Must specify 'other' sexual orientation")
            elif sexual_orien_other:
                raise ValueError(
                    "'sexual_orien_other' should not be specified without 'OT'"
                )
        elif sexual_orien_other:
            raise ValueError(
                "'sexual_orien_other' should not be specified without 'sexual_orien'"
            )
        return self


class AccountPatchSchema(AccountSchema):
    account_id: str = Field(description="Account id of the user's account")
    name: str | None = Field(
        default=None, min_length=1, max_length=250, description="User's name"
    )
    email: str | None = Field(
        default=None, decription="Email which uniquely identifies an account"
    )
    zip: str | None = Field(
        default=None,
        min_length=5,
        max_length=25,
        decription="User's zip code",
    )
    age: int | None = Field(
        default=None, ge=1, le=200, description="User's age"
    )
    is_latino: IsLatinoLabels | None = Field(
        default=None,
        description="""Is the user of Latin descent?
                    <br><br>Choices:
                    <br>YE = Yes
                    <br>NO = No
                    <br>DA = Decline to answer""",
    )
    race: list[RaceLabels] | None = Field(
        default=None,
        description="""User's race.
                        <br><br>Choices:
                        <br>NA = American Indian or Alaska Native
                        <br>BL = Black
                        <br>AS = Asian
                        <br>PI = Native Hawaiian or other Pacific Islander
                        <br>WH = White
                        <br>OT = Other
                        <br>DA = Decline to answer""",
    )
    race_other: str | None = Field(
        default=None,
        max_length=75,
        description="Free-form text field for 'race' value 'OT'",
    )
    gender: GenderLabels | None = Field(
        default=None,
        description="""User's self-identified gender identity.
                    <br><br>Choices:
                    <br>CF = Female
                    <br>CM = Male
                    <br>TF = Trans Female
                    <br>TM = Trans Male
                    <br>NB = Non-binary
                    <br>OT = Other
                    <br>DA = Decline to answer
                """,
    )
    gender_other: str | None = Field(
        default=None,
        max_length=75,
        description="Free-form text field for 'gender' value 'OT'.",
    )
    sexual_orien: SexualOrientationLabels | None = Field(
        default=None,
        description="""Self-identified sexual orientation of user.
                    <br><br>Choices:
                    <br>BS = Bisexual
                    <br>SG = SameGenderLoving
                    <br>US = Unsure
                    <br>HS = Heterosexual
                    <br>OT = Other
                    <br>DA = Decline to answer""",
    )
    sexual_orien_other: str | None = Field(
        default=None,
        max_length=75,
        description="Free-form text field for 'sexual_orien' value 'OT'.",
    )


class ErrorSchema(Schema):
    message: str = Field(
        description="Error message to display",
    )
