from src.logger.logging import setup_logging
from src.tools.utils import parse_arguments


def main():
    args = parse_arguments()
    setup_logging(log_level=args.log_level, log_level_others=args.log_level_other)


if __name__ == "__main__":
    main()
