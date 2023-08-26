from datetime import date, timedelta

DATE_FORMAT = '%Y-%m-%d'


def get_start_of_week(dt: date) -> date:
    return dt - timedelta(days=dt.weekday())


def get_start_of_current_week() -> date:
    dt = date.today()
    return get_start_of_week(dt)
