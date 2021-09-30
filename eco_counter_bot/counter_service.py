import logging

from datetime import date, timedelta
from functools import reduce
from eco_counter_bot.models import DateRange

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

    flattened_count = check_counts
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

    this_week_start = today - timedelta(days=today.weekday())
    this_week_end = today - timedelta(days=1)

    last_week_start = this_week_start - timedelta(weeks=1)
    last_week_relative_end = this_week_end - timedelta(weeks=1)

    counters_with_counts = list(map(lambda counter: {"counter": counter, "counts": get_counts(counter, last_week_start, today, Interval.DAYS)}, counters))
    summed_data = flatten(list(map(lambda counter_with_count: counter_with_count["counts"], counters_with_counts)))

    counters_with_yesterdays_counts = list(map(lambda counter_with_counts: CounterWithSingleCount(counter=counter_with_counts["counter"], count=get_count_for_yesterday(counter_with_counts["counts"])), counters_with_counts))

    yesterdays_counts_sorted = sorted(counters_with_yesterdays_counts, key=lambda count_data: count_data["count"], reverse=True)

    last_week_relative_combined = filter_counts_by_date(summed_data, last_week_start, last_week_relative_end)
    this_week_combined = filter_counts_by_date(summed_data, this_week_start, today)

    last_week_relative_total_count = sum_counts(last_week_relative_combined)
    this_week_total_count = sum_counts(this_week_combined)

    percentage_change = (this_week_total_count - last_week_relative_total_count) / last_week_relative_total_count * 100

    return ProcessedCountData(
        measured_period=DateRange(start=this_week_start, end=this_week_end),
        reference_period=DateRange(start=last_week_start, end=last_week_relative_end),
        ordered_counts=yesterdays_counts_sorted,
        measured_period_total_count=this_week_total_count,
        reference_period_total_count=last_week_relative_total_count,
        percentage_change=percentage_change
    )
