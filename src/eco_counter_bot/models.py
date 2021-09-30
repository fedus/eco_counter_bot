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
