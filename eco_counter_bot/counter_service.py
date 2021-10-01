import logging

from datetime import date
from functools import reduce
from eco_counter_bot.models import CounterConfig, DataPoint, DateRange
from copy import deepcopy

from eco_counter_bot.models import Interval, CounterData, CounterWithSingleCount, CounterWithCounts, CountHighlights
from eco_counter_bot.counter_api import get_counts

logger = logging.getLogger(f"eco_counter_bot.{__name__}")

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
            logger.warn("Likely data mismatch detected during flattening - sums might not be accurate")

    count_with_most_data_points = max(bike_counts, key=lambda bike_count: len(bike_count))

    flattened_count = list(
        map(
            lambda data_point: DataPoint(date=data_point["date"], count=0),
            count_with_most_data_points
        )
    )

    for count in bike_counts:
        for flattened_data_point in flattened_count:
            reference_date = flattened_data_point["date"]

            match_in_count = next(filter(lambda data_point: data_point["date"] == reference_date, count), None)

            if match_in_count:
                flattened_data_point["count"] += match_in_count["count"]
            else:
                logger.warn(f"Missing data point for date {reference_date.strftime('%Y/%m/%d')} while flattening")

    return flattened_count

def filter_counts_by_date(counter_data: CounterData, start_date: date, end_date: date) -> CounterData:
    return list(filter(lambda data_point: start_date <= data_point["date"] <= end_date, counter_data))

def sum_counts(counter_data: CounterData) -> int:
    return reduce(lambda current_sum, data_point: current_sum + data_point["count"], counter_data, 0)

def get_counts_for_period(counters: list[CounterConfig], period: DateRange, interval: Interval = Interval.DAYS) -> list[CounterWithCounts]:
    return list(
        map(
            lambda counter: {"counter": counter, "counts": get_counts(counter, period["start"], period["end"], interval)},
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
