import logging

from django.views.decorators.csrf import csrf_exempt
from ninja import Router
from ninja.errors import HttpError

from home.models import Device, IntentionalWalk
from home.views.apiv2.schemas.intentionalwalk import (
    ErrorSchema,
    IntentionalWalkInSchema,
    IntentionalWalkOutSchema,
)

logger = logging.getLogger(__name__)
router = Router()


@router.get(
    "/{account_id}", response={200: IntentionalWalkOutSchema, 404: ErrorSchema}
)
@csrf_exempt
def get_intentional_walks(request, account_id: str):
    try:
        device = Device.objects.get(device_id=account_id)
    except Device.DoesNotExist:
        raise HttpError(
            404,
            (
                f"Unregistered device - "
                f"{account_id}. "
                f"Please register first!"
            ),
        )
    # Get walks from tied to this account
    # NOTE: This is very hacky and cannot distinguish between legit and
    # fake users.
    # Someone can simply install the app on a new device and use a known
    # email id and have the metrics simply aggregated.
    # For the simple use case, this is likely not an issue and would need
    # to be handled manually if needed
    intentional_walks = IntentionalWalk.objects.filter(account=device.account)

    return 200, {"intentional_walks": list(intentional_walks)}


@router.post("", response={201: IntentionalWalkInSchema, 404: ErrorSchema})
@csrf_exempt
def create_intentional_walk(request, payload: IntentionalWalkInSchema):
    json_data = payload.dict()

    # Get the device if already registered
    try:
        device = Device.objects.get(device_id=json_data["account_id"])
    except Device.DoesNotExist:
        raise HttpError(
            404,
            (
                f"Unregistered device - "
                f"{json_data['account_id']}. "
                f"Please register first!"
            ),
        )
    json_response = {
        "account_id": device.device_id,
        "intentional_walks": [],
    }

    # Loop through all the intentional walks
    for intentional_walk_data in json_data["intentional_walks"]:
        try:
            intentional_walk = IntentionalWalk.objects.create(
                event_id=intentional_walk_data["event_id"],
                start=intentional_walk_data["start"],
                end=intentional_walk_data["end"],
                steps=intentional_walk_data["steps"],
                distance=intentional_walk_data["distance"],
                pause_time=intentional_walk_data["pause_time"],
                device=device,
            )

            json_response["intentional_walks"].append(
                {
                    "event_id": intentional_walk.event_id,
                    "start": intentional_walk.start,
                    "end": intentional_walk.end,
                    "steps": intentional_walk.steps,
                    "distance": intentional_walk.distance,
                    "pause_time": intentional_walk.pause_time,
                }
            )
        except Exception:
            # IntentionalWalk records are immutable- so ignore any errors
            # that might occur if the record already exists, etc...
            pass

    return 201, payload
