import logging
import os
from logging.handlers import TimedRotatingFileHandler

from rich.logging import RichHandler
from src.tools.utils import set_directory_path


def setup_logging(
    log_dir: str = "logs", log_level: str = "INFO", log_level_others: str = "WARNING"
):

    log_dir = set_directory_path(log_dir)
    log_format = os.getenv("LOG_FORMAT", "rich")

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, "alert-rcb.log")

    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    file_handler = TimedRotatingFileHandler(
        log_file,
        when="midnight",
        backupCount=int(os.getenv("LOG_ROTATE_DAYS", 30)),
        encoding="utf-8",
    )
    file_handler.suffix = "%Y-%m-%d"

    handlers: list[logging.Handler] = [file_handler]

    if log_format == "rich":
        handlers.append(
            RichHandler(rich_tracebacks=True, markup=True, show_time=False, show_path=True)
        )
    elif log_format == "plain":
        handlers.append(logging.StreamHandler())
    else:
        handlers.append(logging.StreamHandler())

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(levelname)s - [%(name)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )

    logging.getLogger("urllib3").setLevel(
        getattr(logging, log_level_others.upper(), logging.WARNING)
    )
    logging.getLogger("requests").setLevel(
        getattr(logging, log_level_others.upper(), logging.WARNING)
    )

    logger = logging.getLogger(__name__)
    logger.debug(log_dir)
    logger.debug("Logging module initilized!")

    return logger
