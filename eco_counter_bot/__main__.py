import logging

from datetime import datetime

from eco_counter_bot.config import config
from eco_counter_bot.bot import publish_yesterdays_results

logging.basicConfig(encoding='utf-8')
logger = logging.getLogger(f"eco_counter_bot")
logger.setLevel(config.get("LOG_LEVEL"))

def run():
    logger.info(f"eco_counter_bot started at {datetime.now()}")
    print(publish_yesterdays_results())

if __name__ == "__main__":
    run()
