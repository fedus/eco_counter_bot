from enum import Enum
from typing import TypedDict
from string import Template
from datetime import date

class Interval(Enum):
    DAYS = 4
    WEEKS = 5
    MONTHS = 6

class CounterConfig(TypedDict):
    id: str
    name: str
    url_template: Template

class CounterTemplateValues(TypedDict):
    start_date: str
    end_date: str
    interval: int

class DataPoint(TypedDict):
    date: date
    count: int

CounterData = list[DataPoint]

class DateRange(TypedDict):
    start: date
    end: date

class CounterWithSingleCount(TypedDict):
    counter: CounterConfig
    count: int

class CounterWithCounts(TypedDict):
    counter: CounterConfig
    counts: CounterData

class CountHighlights(TypedDict):
    flattened_counts: CounterData
    most_recent_flattened_count: int
    most_recent_counts_sorted: list[CounterWithSingleCount]
    period_total_count: int

class YesterdaysResultsTweetParams(TypedDict):
    yesterdays_date: str
    count_total: int
    counter_name_1: str
    counter_name_2: str
    counter_name_3: str
    counter_count_1: int
    counter_count_2: int
    counter_count_3: int
    week_reference: str
    count_last_week_total: int
    count_preceding_week_total: int
    percentage_change_emoji: str
    percentage_change_number: float
