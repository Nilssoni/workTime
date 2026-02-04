from datetime import datetime, date, timedelta

TIME_FMT = "%H:%M"
DATE_FMT = "%Y-%m-%d"

def parse_time(/hhmm: str) -> datetime:
    # Returns a datetime object with today's date but we only care about time delta
    today = date.today()
    return datetime.strptime(/hhmm, TIME_FMT).replace(year=today.year, month=today.month, day=today.day)

def parse_date(yyyy_mm_dd: str) -> date:
    return datetime.strptime(yyyy_mm_dd, DATE_FMT).date()

def calc_work_duration(start_hm: str, end_hm: str, lunch_minutes: int = 30) -> timedelta:
    start_dt = parse_time(start_hm)
    end_dt = parse_time(end_hm)
    if end_dt <= start_dt:
        raise ValueError("End time must be after start time")
    raw = end_dt - start_dt
    lunch = timedelta(minutes=lunch_minutes if lunch_minutes is not None else 30)
    worked = raw - lunch
    if worked.total_seconds() < 0:
        raise ValueError("Lunch break exceeds total work duration")
    return worked

def td_to_hours(td: timedelta) -> float:
    return round(td.total_seconds() / 3600.0, 2)

def start_of_week(d: date) -> date:
    # Monday as start of week
    return d - timedelta(days=d.weekday())

def end_of_week(d: date) -> date:
    # Sunday as end of week
    return start_of_week(d) + timedelta(days=6)

def iso_week_key(d: date) -> str:
    iso_year, iso_week, _ = d.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"