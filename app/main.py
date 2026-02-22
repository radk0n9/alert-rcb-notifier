from src.content.content_parser import ContentParser
from src.content.site_content import SiteContent
from src.db_manager.manager import DatabaseManager
from src.logger.logging import setup_logging
from src.tools.utils import parse_arguments


def main():
    args = parse_arguments()
    setup_logging(log_level=args.log_level, log_level_others=args.log_level_other)

    site_content = SiteContent(
        url="https://www.gov.pl/web/rcb/komunikaty",
    )
    site_content.download_all()

    content_parser = ContentParser()
    records = content_parser.parse_all_articles()

    database_manager = DatabaseManager()
    database_manager.init_database()
    database_manager.insert_alerts(records)


if __name__ == "__main__":
    main()
