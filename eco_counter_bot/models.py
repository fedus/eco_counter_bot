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

class ProcessedCountData(TypedDict):
    measured_period: DateRange
    reference_period: DateRange
    ordered_counts: list[CounterWithSingleCount]
    measured_period_total_count: int
    reference_period_total_count: int
    percentage_change: float
