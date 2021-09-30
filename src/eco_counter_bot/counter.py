from enum import Enum
from string import Template
from datetime import date, datetime, timedelta
from typing import TypedDict
from functools import reduce
import requests

class NoDataFoundException(Exception):
    pass

class EcoCounterApiError(Exception):
    pass

class CounterDataMismatch(Exception):
    pass

class Interval(Enum):
    DAYS = 4
    WEEKS = 5
    MONTHS = 6

class CounterConfig(TypedDict):
    name: str
    url_template: Template

class CounterTemplateValues(TypedDict):
    start_date: str
    end_date: str
    interval: int

DataPoint = tuple[date, int]
CounterData = list[DataPoint]

counter_viaduc = CounterConfig(name="viaduc", url_template=Template("https://www.eco-visio.net/api/aladdin/1.0.0/pbl/publicwebpageplus/data/100065111?idOrganisme=4586&idPdc=100065111&fin=$end_date&debut=$start_date&interval=$interval&flowIds=101065111%3B102065111"))
counter_lift = CounterConfig(name="lift",     url_template=Template("https://www.eco-visio.net/api/aladdin/1.0.0/pbl/publicwebpageplus/data/100136902?idOrganisme=4586&idPdc=100136902&fin=$end_date&debut=$start_date&interval=$interval&flowIds=101136902%3B102136902%3B103136902%3B104136902"))
counter_glacis = CounterConfig(name="glacis", url_template=Template("https://www.eco-visio.net/api/aladdin/1.0.0/pbl/publicwebpageplus/data/100136901?idOrganisme=4586&idPdc=100136901&fin=$end_date&debut=$start_date&interval=$interval&flowIds=101136901%3B102136901%3B103136901%3B104136901%3B105136901%3B106136901%3B107136901%3B108136901"))

def parse_date_for_api(date_: date) -> str:
    return date_.strftime("%d/%m/%Y")

def parse_date_from_api(date_: str) -> date:
    return datetime.strptime(date_, "%m/%d/%Y").date()

def get_counts(counter: CounterConfig, start_date: date, end_date: date, interval: Interval) -> CounterData:
    template_values = CounterTemplateValues(
        start_date=parse_date_for_api(start_date),
        end_date=parse_date_for_api(end_date),
        interval=interval.value
    )
    request_url = counter["url_template"].substitute(template_values)
    r = requests.get(request_url)
    if r.status_code != 200:
        raise EcoCounterApiError(f"Error while making request: {r.text}")
    return list(map(lambda datapoint: [parse_date_from_api(datapoint[0]), int(datapoint[1])],r.json()))

def get_count_for_day(counter_data: CounterData, day: date):
    if not len(counter_data):
        raise NoDataFoundException("No data or unexpected data found")
    data_match = next(filter(lambda count: count[0] == day, counter_data), None)
    if not data_match:
        raise NoDataFoundException(f"Requested day not found in returned data, looked for {day}, found {counter_data}")
    return data_match[1]

def get_count_for_yesterday(counter_data: CounterData):
    yesterday = date.today() - timedelta(days=1)
    return get_count_for_day(counter_data, yesterday)

def flatten(*bike_counts: CounterData) -> CounterData:
    check_counts = bike_counts[0]
    check_data_count = len(check_counts)
    check_first_date = check_counts[0][0]
    check_last_date = check_counts[-1][0]
    for bike_count in bike_counts:
        data_count = len(bike_count)
        first_date = bike_count[0][0]
        last_date = bike_count[-1][0]
        if data_count != check_data_count or first_date != check_first_date or last_date != check_last_date:
            raise CounterDataMismatch("Cannot flatten data due to a data mismatch")
    flattened_count = check_counts
    other_counts = bike_counts[1:]
    for other_count in other_counts:
        for index, data_point in enumerate(other_count):
            flattened_count[index][1] += data_point[1]
    return flattened_count

def filter_counts_by_date(counter_data: CounterData, start_date: date, end_date: date) -> CounterData:
    return list(filter(lambda data_point: start_date <= data_point[0] <= end_date, counter_data))

def sum_counts(counter_data: CounterData) -> int:
    return reduce(lambda current_sum, data_point: current_sum + data_point[1], counter_data, 0)

today = date.today()
this_week_start = today - timedelta(days=today.weekday())
this_week_end = today - timedelta(days=1)
last_week_start = this_week_start - timedelta(weeks=1)
last_week_relative_end = this_week_end - timedelta(weeks=1)
print(this_week_start, this_week_end)
print(last_week_start, last_week_relative_end)


glacis_data = get_counts(counter_glacis, last_week_start, today, Interval.DAYS)
viaduc_data = get_counts(counter_viaduc, last_week_start, today, Interval.DAYS)
lift_data = get_counts(counter_lift, last_week_start, today, Interval.DAYS)
summed_data = flatten(glacis_data, viaduc_data, lift_data)

yesterdays_counts = [
    { "counter": "glacis", "count": get_count_for_yesterday(glacis_data) },
    { "counter": "viaduc", "count": get_count_for_yesterday(viaduc_data) },
    { "counter": "lift", "count": get_count_for_yesterday(lift_data) },
]

yesterdays_counts_sorted = sorted(yesterdays_counts, key=lambda count_data: count_data["count"], reverse=True)

last_week_relative_combined = filter_counts_by_date(summed_data, last_week_start, last_week_relative_end)
this_week_combined = filter_counts_by_date(summed_data, this_week_start, today)

last_week_relative_total_count = sum_counts(last_week_relative_combined)
this_week_total_count = sum_counts(this_week_combined)

percentage_change = (this_week_total_count - last_week_relative_total_count) / last_week_relative_total_count * 100

print(yesterdays_counts_sorted)
print(last_week_relative_total_count, this_week_total_count, round(percentage_change, 1))
