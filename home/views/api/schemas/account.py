from ninja import ModelSchema, Schema
from pydantic import field_validator
from typing import Optional

from home.models.account import Account, SAN_FRANCISCO_ZIP_CODES
from home.models.device import Device


class DeviceSchema(ModelSchema):
    class Meta:
        model = Device
        fields = (
                "device_id",
                "account",
                "created"
        )


# class AccountSchema(ModelSchema):
#     account_id: str
#     # is_test: bool
#     # race = list

#     class Meta:
#         model = Account
#         fields = (
#             "name",
#             "email",
#             "zip",
#             "age",
#             "is_latino",
#             "race",
#             "race_other",
#             "gender",
#             "gender_other",
#             "sexual_orien",
#             "sexual_orien_other",
#         )

    # @validator("account_id")
    # def redefine_account_id(cls, v):
    #     return v.device_id

class AccountSchema(Schema):
    account_id: str
    name: str
    email: str
    zip: str
    age: int
    is_latino: Optional[str] = None
    race: Optional[list] = None
    race_other: Optional[str] = None
    gender: Optional[str] = None
    gender_other: Optional[str] = None
    sexual_orien: Optional[str] = None
    sexual_orien_other: Optional[str] = None

    # Check for valid zip code
    @field_validator("zip")
    def check_zip(cls, zipcode):
        if zipcode not in SAN_FRANCISCO_ZIP_CODES:
            raise ValueError("Invalid zip code")
        # assert zipcode in SAN_FRANCISCO_ZIP_CODES, "Invalid zip code"
        return zipcode
    
    # Check for valid age range
    # @validator("age")
    # def valid_
    # ):  # Required field but existence checked in validate_request_json
    #     assert data["age"] > 1 and data["age"] < 200, "Invalid age"
    # if data.get("is_latino") is not None:
    #     is_latino = data["is_latino"]
    #     assert (
    #         is_latino in IsLatinoLabels.__members__
    #     ), f"Invalid is latino or hispanic selection '{is_latino}'"
    # if data.get("race") is not None:
    #     for item in data["race"]:
    #         assert (
    #             item in RaceLabels.__members__
    #         ), f"Invalid race selection '{item}'"
    #     if "OT" in data["race"]:
    #         assert (
    #             len(data.get("race_other", "")) > 0
    #         ), "Must specify 'other' race"
    #     else:
    #         assert (
    #             data.get("race_other") is None
    #         ), "'race_other' should not be specified without race 'OT'"
    # elif data.get("race_other") is not None:
    #     assert False, "'race_other' should not be specified without 'race'"
    # if data.get("gender") is not None:
    #     gender = data["gender"]
    #     assert (
    #         gender in GenderLabels.__members__
    #     ), f"Invalid gender selection '{gender}'"
    #     if data["gender"] == "OT":
    #         assert (
    #             len(data.get("gender_other", "")) > 0
    #         ), "Must specify 'other' gender"
    #     else:
    #         assert (
    #             data.get("gender_other") is None
    #         ), "'gender_other' should not be specified without 'OT'"
    # elif data.get("gender_other") is not None:
    #     assert False, "'gender_other' should not be specified without 'gender'"
    # if data.get("sexual_orien") is not None:
    #     sexual_orientation = data["sexual_orien"]
    #     assert (
    #         sexual_orientation in SexualOrientationLabels.__members__
    #     ), f"Invalid sexual orientation selection '{sexual_orientation}'"
    #     if data["sexual_orien"] == "OT":
    #         assert (
    #             len(data.get("sexual_orien_other", "")) > 0
    #         ), "Must specify 'other' sexual orientation"
    #     else:
    #         assert (
    #             data.get("sexual_orien_other") is None
    #         ), "'sexual_orien_other' should not be specified without 'OT'"
    # elif data.get("sexual_orien_other") is not None:
    #     assert (
    #         False
    #     ), "'sexual_orien_other' should not be specified without 'gender'"
    


# class AccountOut(ModelSchema):
#     class Meta:
#         model = Account
#         fields = (
#             "name",
#             "email",
#             "zip",
#             "age",
#             "is_latino",
#             "race",
#             "race_other",
#             "gender",
#             "gender_other",
#             "sexual_orien",
#             "sexual_orien_other",
#         )


class Error(Schema):
    message: str
