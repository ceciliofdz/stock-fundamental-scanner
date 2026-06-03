from datetime import date, timedelta

def is_today(d: date) -> bool:
    return d == date.today()

def is_tomorrow(d: date) -> bool:
    return d == date.today() + timedelta(days=1)
