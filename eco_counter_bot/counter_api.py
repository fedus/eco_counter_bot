import requests
import logging

from datetime import date, datetime, timedelta

from eco_counter_bot.models import Interval, CounterConfig, CounterTemplateValues, DataPoint, CounterData

logger = logging.getLogger(f"eco_counter_bot.{__name__}")

class NoDataFoundException(Exception):
    pass

class EcoCounterApiError(Exception):
    pass

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

    return list(map(lambda datapoint: DataPoint(date=parse_date_from_api(datapoint[0]), count=int(datapoint[1])),r.json()))

def get_count_for_day(counter_data: CounterData, day: date):
    if not len(counter_data):
        raise NoDataFoundException(f"No data or unexpected data found (requested date {day.strftime('%Y/%m/%d')})")

    data_match = next(filter(lambda count: count["date"] == day, counter_data), None)

    if not data_match:
        raise NoDataFoundException(f"Requested day not found in returned data, looked for {day.strftime('%Y/%m/%d')}, found {counter_data}")

    return data_match["count"]

def get_count_for_yesterday(counter_data: CounterData):
    yesterday = date.today() - timedelta(days=1)
    return get_count_for_day(counter_data, yesterday)
