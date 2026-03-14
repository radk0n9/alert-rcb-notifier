import logging
import os
import time

from src.content.content_parser import ContentParser
from src.content.site_content import SiteContent
from src.db_manager.manager import DatabaseManager
from src.logger.logging import setup_logging
from src.notifier.telegram import TelegramNotifier
from src.tools.utils import load_env, parse_arguments, set_directory_path


def run_test(database_manager: DatabaseManager, logger: logging.Logger):
    record = database_manager.get_latest_record()
    if record:
        logger.info("Test mode: sending latest record from DB: %s", record["title"])
        TelegramNotifier(test=True).send(record)
    else:
        logger.warning("Test mode: no records found in DB")


def run(
    site_content: SiteContent,
    content_parser: ContentParser,
    database_manager: DatabaseManager,
    logger: logging.Logger,
):
    all_new_records = []
    page = 1

    while True:
        html = site_content.fetch_page(page)

        if not html:
            logger.warning("No content returned for page %d, stopping", page)
            break

        records = content_parser.parse_html(html)

        if not records:
            logger.info("No records parsed on page %d, stopping", page)
            break

        new_records = database_manager.filter_new_records(records)
        database_manager.insert_alerts(new_records)
        all_new_records.extend(new_records)

        if not new_records:
            logger.info("No new records on page %d, stopping", page)
            break

        page += 1

    if all_new_records:
        latest = max(all_new_records, key=lambda r: r["date"])
        logger.info("Sending latest alert: %s", latest["title"])
        TelegramNotifier().send(latest)
    else:
        logger.info("No new alerts to send")


def main():
    load_env(set_directory_path("../.env"))
    args = parse_arguments()
    setup_logging(log_level=args.log_level, log_level_others=args.log_level_other)

    logger = logging.getLogger(__name__)

    site_content = SiteContent(url="https://www.gov.pl/web/rcb/komunikaty")
    content_parser = ContentParser()
    database_manager = DatabaseManager()
    database_manager.init_database()
    TelegramNotifier(test=args.test).send_status()

    interval = int(os.getenv("CHECK_INTERVAL", 1800))
    logger.info("Check interval: %ds", interval)

    while True:
        if args.test:
            run_test(database_manager, logger)
        else:
            run(site_content, content_parser, database_manager, logger)

        logger.info("Next check in %ds", interval)
        time.sleep(interval)


if __name__ == "__main__":
    main()
