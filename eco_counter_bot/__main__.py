import logging

from datetime import datetime

from eco_counter_bot.config import config
from eco_counter_bot.bot import publish_yesterdays_results

logging.basicConfig(encoding='utf-8')
logger = logging.getLogger(f"eco_counter_bot")
logger.setLevel(config.get("LOG_LEVEL", "INFO"))

def run() -> None:
    logger.info(f"eco_counter_bot started at {datetime.now()}")
    publish_yesterdays_results()
    logger.info(f"Run finished at {datetime.now()}")

if __name__ == "__main__":
    run()
