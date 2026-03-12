import logging
import os
from datetime import datetime

from rich.logging import RichHandler
from src.tools.utils import set_directory_path


def setup_logging(
    log_dir: str = "logs", log_level: str = "INFO", log_level_others: str = "WARNING"
):

    log_dir = set_directory_path(log_dir)
    log_format = os.getenv("LOG_FORMAT", "rich")

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"log_{timestamp}.log")

    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    handlers: list[logging.Handler] = []
    handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

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

    logger = logging.getLogger(__name__)
    logger.info("Logging module initilized!")

    return logger
