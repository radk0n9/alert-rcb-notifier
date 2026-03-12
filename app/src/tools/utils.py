import argparse
import logging
import os
from dataclasses import dataclass

from dotenv import dotenv_values, load_dotenv

logger = logging.getLogger(__name__)


def set_directory_path(desired_path: str):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    logger.debug("Project root directory: '%s'", project_root)
    requested_path = os.path.join(project_root, desired_path)
    logger.debug("Requested directory path: '%s'", requested_path)
    return requested_path


def load_env(env_file_path: str):
    try:
        env_loaded = load_dotenv(env_file_path, override=False)
        if env_loaded:
            logger.info("Enironment variables loaded from config file '%s'", env_file_path)
            env_values = dotenv_values(env_file_path)
            for key, value in env_values.items():
                logger.debug("Loaded env var: %s=%s", key, value)
    except Exception as e:
        logger.exception("Error loading environment variables from file '%s': %s", env_file_path, e)


@dataclass
class ParserArgument:
    log_level: str
    log_level_other: str
    test: bool


def parse_arguments() -> ParserArgument:
    parser = argparse.ArgumentParser(prog="Alert RCB")

    parser.add_argument(
        "-l", "--log-level", default=os.getenv("LOG_LEVEL", "INFO"), help="Logging level"
    )
    parser.add_argument(
        "-lo",
        "--log-level-others",
        default=os.getenv("LOG_LEVEL_OTHERS", "WARNING"),
        help="Logging level others",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Send the latest alert from DB without fetching new data",
    )

    args = parser.parse_args()

    return ParserArgument(log_level=args.log_level, log_level_other=args.log_level_others, test=args.test)
