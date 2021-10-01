import requests
import logging

from datetime import date, datetime, timedelta

from eco_counter_bot.models import Interval, CounterConfig, CounterTemplateValues, DataPoint, CounterData

logger = logging.getLogger(f"eco_counter_bot.{__name__}")

class EcoCounterApiError(Exception):
    pass

def parse_date_for_api(date_: date) -> str:
    return date_.strftime("%d/%m/%Y")

def parse_date_from_api(date_: str) -> date:
    return datetime.strptime(date_, "%m/%d/%Y").date()

def get_counts(counter: CounterConfig, start_date: date, end_date: date, interval: Interval) -> CounterData:
    exclusive_end_date_for_api = end_date + timedelta(days=1)

    template_values = CounterTemplateValues(
        start_date=parse_date_for_api(start_date),
        end_date=parse_date_for_api(exclusive_end_date_for_api),
        interval=interval.value
    )

    request_url = counter["url_template"].substitute(template_values)

    logger.debug(f"Attempting API request with template values {template_values} and request url {request_url}")

    r = requests.get(request_url)

    if r.status_code != 200:
        raise EcoCounterApiError(f"Error while making request: {r.text}")

    return list(map(lambda datapoint: DataPoint(date=parse_date_from_api(datapoint[0]), count=int(datapoint[1])),r.json()))

