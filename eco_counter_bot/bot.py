import logging

from string import Template
from datetime import date, timedelta

from eco_counter_bot.models import YesterdaysResultsTweetParams
from eco_counter_bot.counter_api import NoDataFoundException
from eco_counter_bot.counter_service import get_yesterdays_info
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

def publish_yesterdays_results():
    try:
        logger.debug("Attempting to get yesterday's info")
        yesterdays_info = get_yesterdays_info()
    except NoDataFoundException as e:
        logger.warning(e, exc_info=True)
        return
    except Exception as e:
        logger.error(f"Encountered unexpected error, aborting. {e}", exc_info=True)
        return

    yesterday = date.today() - timedelta(days=1)

    logger.debug(f"Yesterday's date is {yesterday}")

    tweet_template_params = YesterdaysResultsTweetParams(
        yesterdays_date = yesterday.strftime("%d/%m"),
        count_total = yesterdays_info["ordered_counts_total"],
        counter_name_1 = yesterdays_info["ordered_counts"][0]["counter"]["name"],
        counter_name_2 = yesterdays_info["ordered_counts"][1]["counter"]["name"],
        counter_name_3 = yesterdays_info["ordered_counts"][2]["counter"]["name"],
        counter_count_1 = yesterdays_info["ordered_counts"][0]["count"],
        counter_count_2 = yesterdays_info["ordered_counts"][1]["count"],
        counter_count_3 = yesterdays_info["ordered_counts"][2]["count"],
        week_reference = "This" if is_current_week(yesterday) else "Last",
        count_last_week_total = yesterdays_info["measured_period_total_count"],
        count_preceding_week_total = yesterdays_info["reference_period_total_count"],
        percentage_change_emoji = EMOJIS["DOWN_RIGHT_ARROW"] if yesterdays_info["percentage_change"] < 0 else EMOJIS["UP_RIGHT_ARROW"],
        percentage_change_number = round(yesterdays_info["percentage_change"], 1)
    )

    logger.debug(f"Assembled tweet params: {tweet_template_params}")

    tweet_message = TWEET_TEMPLATE.substitute(tweet_template_params)

    logger.debug(f"Assembled tweet message: {tweet_message}")

    try:
        logger.debug("Attempting to tweet")
        tweet_service.tweet_thread(tweet_message)
    except Exception as e:
        logger.error(f"Error while tweeting: {e}", exc_info=True)
