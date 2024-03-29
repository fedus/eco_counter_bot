import logging

from string import Template
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

from eco_counter_bot.utils import format_number_lb
from eco_counter_bot.counters import counters as all_counters
from eco_counter_bot.models import CounterData, DataPoint, DateRange, Interval, YesterdaysResultsTweetParams
from eco_counter_bot.counter_service import NoDataFoundException, get_counts_for_period, extract_highlights
from eco_counter_bot.tweet_service import tweet_service
from eco_counter_bot.grapher import generate_yearly_plot
from eco_counter_bot.emojis import EMOJIS

logger = logging.getLogger(f"eco_counter_bot.{__name__}")

TWEET_TEMPLATE = Template(f"""Yesterday's {EMOJIS['BICYCLE']} counts ($yesterdays_date):

{EMOJIS['CHECKERED_FLAG']} Total: $count_total

Top 3:
{EMOJIS['MEDAL_1']} $counter_name_1: $counter_count_1
{EMOJIS['MEDAL_2']} $counter_name_2: $counter_count_2
{EMOJIS['MEDAL_3']} $counter_name_3: $counter_count_3

$year_reference year's total: $count_current_year_total
Preceding year's total: $count_preceding_year_total
Preceding year's relative total: $count_preceding_year_relative_total
Change: $percentage_change_emoji $percentage_change_number%

$more_or_missing_text
""")

MORE_TEXT = Template(f"$more more than last year's total! {EMOJIS['PARTY']}")
MISSING_TEXT = Template(f"$missing missing compared to last year's total!")

def is_current_week(reference_date: date) -> bool:
    reference_date_week = reference_date.isocalendar().week
    todays_date_week = date.today().isocalendar().week
    return reference_date_week == todays_date_week

def is_current_year(reference_date: date) -> bool:
    return reference_date.year == date.today().year

def to_daily_total(counter_data: CounterData) -> CounterData:
    summed = [counter_data[0]]

    for index, current_count in enumerate(counter_data):
        if index > 0:
            dp = DataPoint(
                date=current_count["date"],
                count=(summed[index-1]["count"] + current_count["count"])
            )

            summed.append(dp)

    return summed

def publish_yesterdays_results() -> None:
    today = date.today()
    yesterday = today - timedelta(days=1)

    current_week = DateRange(
        start=yesterday - timedelta(days=yesterday.weekday()),
        end=yesterday
    )

    current_year_relative = DateRange(
        start=yesterday.replace(month=1, day=1),
        end=yesterday
    )

    preceding_year_relative = DateRange(
        start=yesterday.replace(year=yesterday.year - 1, month=1, day=1),
        end=yesterday + relativedelta(years=-1)
    )

    preceding_year_full = DateRange(
        start=yesterday.replace(year=yesterday.year - 1, month=1, day=1),
        end=yesterday.replace(year=yesterday.year - 1, month=12, day=31)
    )

    try:
        logger.debug("Attempting to get highlights")
        current_week_counts = get_counts_for_period(all_counters, current_week, Interval.DAYS)
        current_year_counts = get_counts_for_period(all_counters, current_year_relative, Interval.DAYS)
        preceding_year_relative_counts = get_counts_for_period(all_counters, preceding_year_relative, Interval.MONTHS)
        preceding_year_full_counts = get_counts_for_period(all_counters, preceding_year_full, Interval.DAYS)

        current_week_highlights = extract_highlights(current_week_counts)
        current_year_highlights = extract_highlights(current_year_counts)
        preceding_year_relative_highlights = extract_highlights(preceding_year_relative_counts)
        preceding_year_full_highlights = extract_highlights(preceding_year_full_counts)
    except NoDataFoundException as e:
        logger.warning(e, exc_info=True)
        return
    except Exception as e:
        logger.error(f"Encountered unexpected error, aborting. {e}", exc_info=True)
        return

    logger.debug(f"Yesterday's date is {yesterday}")

    percentage_change = (current_year_highlights["period_total_count"] - preceding_year_relative_highlights["period_total_count"]) / preceding_year_relative_highlights["period_total_count"] * 100

    yesterdays_ordered_counts = current_week_highlights["most_recent_counts_sorted"]

    excess_compared_to_last_year = current_year_highlights["period_total_count"] - preceding_year_full_highlights["period_total_count"]

    more_or_missing_text = MORE_TEXT.substitute({ "more": format_number_lb(excess_compared_to_last_year) }) \
        if excess_compared_to_last_year >= 0 else MISSING_TEXT.substitute({ "missing": format_number_lb(abs(excess_compared_to_last_year)) })

    tweet_template_params = YesterdaysResultsTweetParams(
        yesterdays_date = yesterday.strftime("%d/%m"),
        count_total = format_number_lb(current_week_highlights["most_recent_flattened_count"]),
        counter_name_1 = yesterdays_ordered_counts[0]["counter"]["name"],
        counter_name_2 = yesterdays_ordered_counts[1]["counter"]["name"],
        counter_name_3 = yesterdays_ordered_counts[2]["counter"]["name"],
        counter_count_1 = format_number_lb(yesterdays_ordered_counts[0]["count"]),
        counter_count_2 = format_number_lb(yesterdays_ordered_counts[1]["count"]),
        counter_count_3 = format_number_lb(yesterdays_ordered_counts[2]["count"]),
        year_reference = "This" if is_current_year(yesterday) else "Last",
        count_current_year_total = format_number_lb(current_year_highlights["period_total_count"]),
        count_preceding_year_total = format_number_lb(preceding_year_full_highlights["period_total_count"]),
        count_preceding_year_relative_total = format_number_lb(preceding_year_relative_highlights["period_total_count"]),
        percentage_change_emoji = EMOJIS["DOWN_RIGHT_ARROW"] if percentage_change < 0 else EMOJIS["UP_RIGHT_ARROW"],
        percentage_change_number = format_number_lb(round(percentage_change, 1)),
        more_or_missing_text = more_or_missing_text
    )

    logger.debug(f"Assembled tweet params: {tweet_template_params}")

    tweet_message = TWEET_TEMPLATE.substitute(tweet_template_params)

    logger.info(f"Assembled tweet message: {tweet_message}")

    preceding_year_daily_total = to_daily_total(preceding_year_full_highlights["flattened_counts"])
    current_year_daily_total = to_daily_total(current_year_highlights["flattened_counts"])

    generate_yearly_plot(preceding_year_daily_total, current_year_daily_total)

    try:
        logger.debug("Attempting to tweet")
        tweet_service.tweet_thread(tweet_message, media_filename="tmp/daily_fig.png")
    except Exception as e:
        logger.error(f"Error while tweeting: {e}", exc_info=True)
