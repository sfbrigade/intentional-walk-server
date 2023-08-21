from datetime import datetime, timedelta

def get_start_of_week(date: datetime.date) -> datetime.date:
    return date - timedelta(days=date.weekday())

def get_start_of_current_week() -> datetime.date:
    date = datetime.date.today()
    return get_start_of_week(date)
