import logging

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from functools import reduce
from eco_counter_bot.models import CounterConfig, DateRange
from copy import deepcopy

from eco_counter_bot.models import Interval, CounterData, CounterWithSingleCount, CounterWithCounts, CountHighlights
from eco_counter_bot.counter_api import get_counts

logger = logging.getLogger(f"eco_counter_bot.{__name__}")

class CounterDataMismatch(Exception):
    pass

class NoDataFoundException(Exception):
    pass

def get_count_for_day(counter_data: CounterData, day: date) -> int:
    if not len(counter_data):
        raise NoDataFoundException(f"No data or unexpected data found (requested date {day.strftime('%Y/%m/%d')})")

    data_match = next(filter(lambda count: count["date"] == day, counter_data), None)

    if not data_match:
        raise NoDataFoundException(f"Requested day not found in returned data, looked for {day.strftime('%Y/%m/%d')}, found {counter_data}")

    return data_match["count"]

def flatten(bike_counts: list[CounterData]) -> CounterData:
    check_counts = bike_counts[0]
    check_data_count = len(check_counts)
    check_first_date = check_counts[0]["date"]
    check_last_date = check_counts[-1]["date"]

    for bike_count in bike_counts:
        data_count = len(bike_count)
        first_date = bike_count[0]["date"]
        last_date = bike_count[-1]["date"]

        if data_count != check_data_count or first_date != check_first_date or last_date != check_last_date:
            raise CounterDataMismatch("Cannot flatten data due to a data mismatch")

    flattened_count = deepcopy(check_counts)
    other_counts = bike_counts[1:]

    for other_count in other_counts:
        for index, data_point in enumerate(other_count):
            flattened_count[index]["count"] += data_point["count"]

    return flattened_count

def filter_counts_by_date(counter_data: CounterData, start_date: date, end_date: date) -> CounterData:
    return list(filter(lambda data_point: start_date <= data_point["date"] <= end_date, counter_data))

def sum_counts(counter_data: CounterData) -> int:
    return reduce(lambda current_sum, data_point: current_sum + data_point["count"], counter_data, 0)

def get_counts_for_period(counters: list[CounterConfig], period: DateRange) -> list[CounterWithCounts]:
    return list(
        map(
            lambda counter: {"counter": counter, "counts": get_counts(counter, period["start"], period["end"], Interval.DAYS)},
            counters
        )
    )

def extract_highlights(counters_with_counts: list[CounterWithCounts]) -> CountHighlights:
    flattened_counts = flatten(list(map(lambda counter_with_counts: counter_with_counts["counts"], counters_with_counts)))

    most_recent_date, most_recent_flattened_count = flattened_counts[-1]["date"], flattened_counts[-1]["count"]

    counters_with_most_recent_counts = list(map(lambda counter_with_counts: CounterWithSingleCount(counter=counter_with_counts["counter"], count=get_count_for_day(counter_with_counts["counts"], most_recent_date)), counters_with_counts))
    most_recent_counts_sorted = sorted(counters_with_most_recent_counts, key=lambda count_data: count_data["count"], reverse=True)

    return CountHighlights(
        flattened_counts=flattened_counts,
        most_recent_flattened_count=most_recent_flattened_count,
        most_recent_counts_sorted=most_recent_counts_sorted,
        period_total_count=sum_counts(flattened_counts)
    )
