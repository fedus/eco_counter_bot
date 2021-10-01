import logging

from string import Template
from datetime import date, timedelta

from eco_counter_bot.counters import counters as all_counters
from eco_counter_bot.models import CountHighlights, DateRange, YesterdaysResultsTweetParams
from eco_counter_bot.counter_service import NoDataFoundException, get_counts_for_period, extract_highlights
from eco_counter_bot.tweet_service import tweet_service
from eco_counter_bot.emojis import EMOJIS

logger = logging.getLogger(f"eco_counter_bot.{__name__}")

TWEET_TEMPLATE = Template(f"""Yesterday’s {EMOJIS['BICYCLE']} counts ($yesterdays_date):

{EMOJIS['CHECKERED_FLAG']} Total: $count_total

{EMOJIS['MEDAL_1']} $counter_name_1: $counter_count_1
{EMOJIS['MEDAL_2']} $counter_name_2: $counter_count_2
{EMOJIS['MEDAL_3']} $counter_name_3: $counter_count_3

$week_reference week’s total: $count_last_week_total
Same period of preceding week’s total: $count_preceding_week_total
Percentage change: $percentage_change_emoji $percentage_change_number
""")

def is_current_week(reference_date: date) -> bool:
    reference_date_week = reference_date.isocalendar().week
    todays_date_week = date.today().isocalendar().week
    return reference_date_week == todays_date_week

def get_highlights_for_period(period: DateRange) -> CountHighlights:
    counters_with_counts = get_counts_for_period(all_counters, period)
    return extract_highlights(counters_with_counts)

def publish_yesterdays_results() -> None:
    today = date.today()
    yesterday = today - timedelta(days=1)

    current_period = DateRange(
        start=yesterday - timedelta(days=yesterday.weekday()),
        end=yesterday
    )

    reference_period = DateRange(
        start=current_period["start"] - timedelta(weeks=1),
        end=current_period["end"] - timedelta(weeks=1)
    )

    try:
        logger.debug("Attempting to get highlights")
        current_period_highlights = get_highlights_for_period(current_period)
        reference_period_highlights = get_highlights_for_period(reference_period)
    except NoDataFoundException as e:
        logger.warning(e, exc_info=True)
        return
    except Exception as e:
        logger.error(f"Encountered unexpected error, aborting. {e}", exc_info=True)
        return

    logger.debug(f"Yesterday's date is {yesterday}")

    percentage_change = (current_period_highlights["period_total_count"] - reference_period_highlights["period_total_count"]) / current_period_highlights["period_total_count"] * 100

    yesterdays_ordered_counts = current_period_highlights["most_recent_counts_sorted"]

    tweet_template_params = YesterdaysResultsTweetParams(
        yesterdays_date = yesterday.strftime("%d/%m"),
        count_total = current_period_highlights["most_recent_flattened_count"],
        counter_name_1 = yesterdays_ordered_counts[0]["counter"]["name"],
        counter_name_2 = yesterdays_ordered_counts[1]["counter"]["name"],
        counter_name_3 = yesterdays_ordered_counts[2]["counter"]["name"],
        counter_count_1 = yesterdays_ordered_counts[0]["count"],
        counter_count_2 = yesterdays_ordered_counts[1]["count"],
        counter_count_3 = yesterdays_ordered_counts[2]["count"],
        week_reference = "This" if is_current_week(yesterday) else "Last",
        count_last_week_total = current_period_highlights["period_total_count"],
        count_preceding_week_total = reference_period_highlights["period_total_count"],
        percentage_change_emoji = EMOJIS["DOWN_RIGHT_ARROW"] if percentage_change < 0 else EMOJIS["UP_RIGHT_ARROW"],
        percentage_change_number = round(percentage_change, 1)
    )

    logger.debug(f"Assembled tweet params: {tweet_template_params}")

    tweet_message = TWEET_TEMPLATE.substitute(tweet_template_params)

    logger.info(f"Assembled tweet message: {tweet_message}")

    try:
        logger.debug("Attempting to tweet")
        tweet_service.tweet_thread(tweet_message)
    except Exception as e:
        logger.error(f"Error while tweeting: {e}", exc_info=True)
