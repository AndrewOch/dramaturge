from datetime import timedelta

from hors.partial_date.partial_datetime import PartialDateTime


def merge_dates(d1: PartialDateTime, d2: PartialDateTime) -> PartialDateTime:
    year = d1.year if d1.year is not None else d2.year
    month = d1.month if d1.month is not None else d2.month
    day = d1.day if d1.day is not None else d2.day
    hour = d1.hour if d1.hour is not None else d2.hour
    minute = d1.minute if d1.minute is not None else d2.minute
    second = d1.second if d1.second is not None else d2.second
    microsecond = d1.microsecond if d1.microsecond is not None else d2.microsecond
    weekday = d1.weekday if d1.weekday is not None else d2.weekday

    known = {
        'day': (year is not None and month is not None and day is not None),
        'hour': (hour is not None),
        'minute': (minute is not None),
        'second': (second is not None),
        'microsecond': (microsecond is not None)
    }

    def mask_offset(offset: timedelta, known):

        days = offset.days if not known['day'] else 0

        sec_total = offset.seconds
        hours = sec_total // 3600
        rem = sec_total % 3600
        minutes = rem // 60
        seconds_part = rem % 60

        if known['hour']:
            hours = 0

        if known['minute']:
            minutes = 0

        if known['second']:
            seconds_part = 0

        micro = offset.microseconds if not known['microsecond'] else 0

        return timedelta(days=days, seconds=hours * 3600 + minutes * 60 + seconds_part, microseconds=micro)

    offset1 = mask_offset(d1.relative_offset, known) if d1.relative_offset is not None else timedelta(0)
    offset2 = mask_offset(d2.relative_offset, known) if d2.relative_offset is not None else timedelta(0)
    merged_offset = offset1 + offset2

    new_date = PartialDateTime(
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        second=second,
        microsecond=microsecond,
        relative_offset=merged_offset,
        weekday=weekday
    )

    if new_date.is_complete():
        new_date = new_date + merged_offset

    return new_date
