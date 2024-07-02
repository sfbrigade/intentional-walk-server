import json
from datetime import date
from typing import List

from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.errors import HttpError

from home.models import Account, Device
from home.models.account import (
    SAN_FRANCISCO_ZIP_CODES,
    GenderLabels,
    IsLatinoLabels,
    RaceLabels,
    SexualOrientationLabels,
)
from home.views.api.schemas.account import AccountSchema, DeviceSchema

router = Router()


# Determines whether Account is tester account, based on name prefix
def is_tester(name_field: str) -> bool:
    possible_prefixes = ["tester-", "tester ", "tester_"]
    return any(
        [name_field.lower().startswith(prefix) for prefix in possible_prefixes]
    )


def update_account(account: Account, json_data: dict):
    # Data fields vary based on registration screen
    for attr, value in json_data.items():
        if attr != "email":
            setattr(account, attr, value)
    account.save()


@router.post("/appuser", response={201: AccountSchema})
def create_appuser(request, payload: AccountSchema):
    # Parse the body json
    json_data = payload.dict()
    # For a participating device
    try:
        # NOTE: Account id here maps to a device id. Perhaps the API
        # definition could be changed in the future.
        # Get the registered device if it exists
        device = Device.objects.get(device_id=json_data["account_id"])
        # If it is an email update fail and return
        if device.account.email.lower() != json_data["email"].lower():
            raise HttpError(400, "Email cannot be updated. Contact admin")

        # Otherwise, update the account's other details
        account = Account.objects.get(email__iexact=json_data["email"])
        update_account(account, json_data)
        return 201, {"account_id": device.device_id, **account.__dict__}

    # This implies that it is a new device
    except Device.DoesNotExist:
        # Check if the user account exists. If not, create it
        try:
            account = Account.objects.get(email__iexact=json_data["email"])
            update_account(account, json_data)
            message = "Account updated successfully"
            account_updated = True
        except Account.DoesNotExist:
            # Partially create account first, with required fields
            account = Account.objects.create(
                email=json_data["email"],
                name=json_data["name"],
                zip=json_data["zip"],
                age=json_data["age"],
                is_tester=is_tester(json_data["name"]),
                is_sf_resident=json_data["zip"] in SAN_FRANCISCO_ZIP_CODES,
            )
            account_updated = False

        # Create a new device object and link it to the account
        device = Device.objects.create(
            device_id=json_data["account_id"], account=account
        )
    
    # return 201, {
    #                 "account_id": device.device_id,
    #                 "name": account.name,
    #                 "email": account.email,
    #                 "zip": account.zip,
    #                 "age": account.age,
    #                 "is_latino": account.is_latino,
    #                 "race": account.race,
    #                 "race_other": account.race_other,
    #                 "gender": account.gender,
    #                 "gender_other": account.gender_other,
    #                 "sexual_orien": account.sexual_orien,
    #                 "sexual_orien_other": account.sexual_orien_other,
    #             }

    return 201, {"account_id": device.device_id, **account.__dict__}


# @router.get("/employees/{employee_id}", response=EmployeeOut)
# def get_employee(request, employee_id: int):
#     employee = get_object_or_404(Employee, id=employee_id)
#     return employee


# @router.get("/employees", response=List[EmployeeOut])
# def list_employees(request):
#     qs = Employee.objects.all()
#     return qs


@router.put("/appuser/{account_id}")
def update_appuser(request, account_id: int, payload: AccountSchema):
    account = get_object_or_404(Account, id=account_id)
    for attr, value in payload.dict().items():
        setattr(account, attr, value)
    account.save()
    return account


@router.delete("/appuser/{account_id}")
def delete_appuser(request, account_id: int):
    account = get_object_or_404(Account, id=account_id)
    account.delete()
    return {"success": True}
