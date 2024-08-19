from django.views.decorators.csrf import csrf_exempt
from ninja import Router
from ninja.errors import HttpError

from home.models import Account, Device
from home.models.account import SAN_FRANCISCO_ZIP_CODES
from home.views.apiv2.schemas.account import (
    AccountPatchSchema,
    AccountSchema,
    ErrorSchema,
)

router = Router()


# Determines whether Account is tester account, based on name prefix
def is_tester(name_field: str) -> bool:
    possible_prefixes = ["tester-", "tester ", "tester_"]
    return any(
        [name_field.lower().startswith(prefix) for prefix in possible_prefixes]
    )


def update_model(account: Account, json_data: dict):
    # Data fields vary based on registration screen
    for attr, value in json_data.items():
        if attr != "email":
            setattr(account, attr, value)
    account.save()


@router.post("", response={201: AccountSchema, 400: ErrorSchema})
@csrf_exempt
def create_appuser(request, payload: AccountSchema):
    # Parse the body json
    json_data = payload.dict()

    # Update user attributes if the object exists, else create.
    # EMAIL CANNOT BE UPDATED!
    # NOTE: Ideally, email ids should be validated by actually sending
    # emails. Currently, accidental/intentional use of the same email id
    # will share data across devices. In such an instance, a new account
    # with the correct email must be created to separate data. Otherwise,
    # attribution will be to the account email created first.

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
        update_model(account, json_data)

        return 201, payload
    # This implies that it is a new device
    except Device.DoesNotExist:
        # Check if the user account exists. If not, create it
        try:
            account = Account.objects.get(email__iexact=json_data["email"])
            update_model(account, json_data)
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

        # Create a new device object and link it to the account
        device = Device.objects.create(
            device_id=json_data["account_id"], account=account
        )

    return 201, payload


@router.put("/{account_id}", response={204: None, 404: ErrorSchema})
@csrf_exempt
def update_appuser(request, account_id: str, payload: AccountSchema):
    json_data = payload.dict()
    try:
        device = Device.objects.get(device_id=account_id)
        # If it is an email update, fail and return
        if device.account.email.lower() != json_data["email"].lower():
            raise HttpError(400, "Email cannot be updated. Contact admin")
    except Device.DoesNotExist:
        raise HttpError(
            404, f"Cannot find device registered with account_id: {account_id}"
        )
    account = Account.objects.get(email__iexact=device.account.email)
    update_model(account, json_data)

    return 204, None


@router.patch("/{account_id}", response={204: None, 404: ErrorSchema})
@csrf_exempt
def update_appuser(request, account_id: str, payload: AccountPatchSchema):
    json_data = payload.dict()
    try:
        device = Device.objects.get(device_id=account_id)
        # If it is an email update, fail and return
        if (
            json_data["email"]
            and device.account.email.lower() != json_data["email"].lower()
        ):
            raise HttpError(400, "Email cannot be updated. Contact admin")
    except Device.DoesNotExist:
        raise HttpError(
            404, f"Cannot find device registered with account_id: {account_id}"
        )
    account = Account.objects.get(email__iexact=device.account.email)
    update_model(account, payload.dict(exclude_unset=True))

    return 204, None


@router.delete("/{account_id}", response={204: None, 404: ErrorSchema})
@csrf_exempt
def delete_appuser(request, account_id: str):
    try:
        device = Device.objects.get(device_id=account_id)
    except Device.DoesNotExist:
        raise HttpError(
            404, f"Cannot find device registered with account_id: {account_id}"
        )
    device.account.delete()
    device.delete()

    return 204, None
