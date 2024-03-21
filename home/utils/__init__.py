from datetime import date, datetime

from django.utils import timezone


# This function converts a date into a datetime based on the default time zone
# (TIME_ZONE, which set in server/settings.py but overridden in .env).
# This is particularly useful for comparing dates to datetimes in db queries.
def localize(d: date) -> datetime:
    dt = datetime.combine(d, datetime.min.time())
    tz = timezone.get_default_timezone()
    return dt.astimezone(tz)
