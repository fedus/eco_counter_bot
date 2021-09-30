import logging

from datetime import date, timedelta
from functools import reduce
from eco_counter_bot.models import DateRange
from copy import deepcopy

from eco_counter_bot.models import Interval, CounterData, CounterWithSingleCount, ProcessedCountData
from eco_counter_bot.counter_api import get_counts, get_count_for_yesterday
from eco_counter_bot.counters import counters

logger = logging.getLogger(f"eco_counter_bot.{__name__}")

class CounterDataMismatch(Exception):
    pass

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

def get_yesterdays_info():
    today = date.today()
    yesterday = today - timedelta(days=1)

    yesterdays_week_start = yesterday - timedelta(days=yesterday.weekday())
    yesterdays_week_relative_end = yesterday

    preceding_week_start = yesterdays_week_start - timedelta(weeks=1)
    preceding_week_relative_end = yesterdays_week_relative_end - timedelta(weeks=1)

    counters_with_counts = list(map(lambda counter: {"counter": counter, "counts": get_counts(counter, preceding_week_start, today, Interval.DAYS)}, counters))
    summed_data = flatten(list(map(lambda counter_with_count: counter_with_count["counts"], counters_with_counts)))

    yesterdays_total = summed_data[-1]["count"]

    counters_with_yesterdays_counts = list(map(lambda counter_with_counts: CounterWithSingleCount(counter=counter_with_counts["counter"], count=get_count_for_yesterday(counter_with_counts["counts"])), counters_with_counts))

    yesterdays_counts_sorted = sorted(counters_with_yesterdays_counts, key=lambda count_data: count_data["count"], reverse=True)

    preceeding_week_relative_combined = filter_counts_by_date(summed_data, preceding_week_start, preceding_week_relative_end)
    yesterdays_week_combined = filter_counts_by_date(summed_data, yesterdays_week_start, today)

    preceeding_week_relative_total_count = sum_counts(preceeding_week_relative_combined)
    yesterdays_week_total_count = sum_counts(yesterdays_week_combined)

    percentage_change = (yesterdays_week_total_count - preceeding_week_relative_total_count) / preceeding_week_relative_total_count * 100

    return ProcessedCountData(
        measured_period=DateRange(start=yesterdays_week_start, end=yesterdays_week_relative_end),
        reference_period=DateRange(start=preceding_week_start, end=preceding_week_relative_end),
        ordered_counts=yesterdays_counts_sorted,
        ordered_counts_total=yesterdays_total,
        measured_period_total_count=yesterdays_week_total_count,
        reference_period_total_count=preceeding_week_relative_total_count,
        percentage_change=percentage_change
    )
