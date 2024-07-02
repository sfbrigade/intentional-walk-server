from django.views.decorators.csrf import csrf_exempt
from ninja import Router
from ninja.errors import HttpError

from home.models import Device
from home.views.apiv2.schemas.device import DeviceInSchema, ErrorSchema

router = Router()


def update_model(device: Device, json_data: dict):
    # Data fields vary based on registration screen
    for attr, value in json_data.items():
        if attr != "email":
            setattr(device, attr, value)
    device.save()


@router.put("/{device_id}", response={204: None, 404: ErrorSchema})
@csrf_exempt
def update_device(request, device_id: str, payload: DeviceInSchema):
    try:
        device = Device.objects.get(device_id=device_id)
    except Device.DoesNotExist:
        raise HttpError(
            404,
            f"""Unregistered device -
                device_id: {device_id}
                Please register first!""",
        )
    update_model(device, payload.dict())

    return 204, None


@router.patch("/{device_id}", response={204: None, 404: ErrorSchema})
@csrf_exempt
def patch_device(request, device_id: str, payload: DeviceInSchema):
    try:
        device = Device.objects.get(device_id=device_id)
    except Device.DoesNotExist:
        raise HttpError(
            404,
            (
                f"Unregistered device - "
                f"{device_id}. "
                f"Please register first!"
            ),
        )
    update_model(device, payload.dict(exclude_unset=True))

    return 204, None


@router.delete("/{device_id}", response={204: None, 404: ErrorSchema})
@csrf_exempt
def delete_device(request, device_id: str):
    try:
        device = Device.objects.get(device_id=device_id)
    except Device.DoesNotExist:
        raise HttpError(
            404,
            (
                f"Unregistered device - "
                f"{device_id}. "
                f"Please register first!"
            ),
        )
    device.account.delete()
    device.delete()

    return 204, None
