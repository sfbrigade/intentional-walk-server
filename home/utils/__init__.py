from datetime import date, datetime, timedelta
from django.http import HttpResponse
from django.utils import timezone


def localize(d: date) -> datetime:
    dt = datetime.combine(d, datetime.min.time())
    tz = timezone.get_default_timezone()
    return tz.localize(dt)
