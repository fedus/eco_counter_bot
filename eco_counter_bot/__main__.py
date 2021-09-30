import logging

from datetime import datetime

from eco_counter_bot.config import config
from eco_counter_bot.counter_service import get_yesterdays_info

logging.basicConfig(encoding='utf-8')
logger = logging.getLogger(f"eco_counter_bot")
logger.setLevel(config.get("LOG_LEVEL"))

def run():
    logger.info(f"eco_counter_bot started at {datetime.now()}")
    print(get_yesterdays_info())

if __name__ == "__main__":
    run()
