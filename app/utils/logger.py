import logging
from pathlib import Path


LOG_FOLDER = Path("logs")

LOG_FOLDER.mkdir(
    exist_ok=True
)

logging.basicConfig(
    filename="logs/application.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)


def log_info(message):

    logging.info(message)


def log_error(message):

    logging.error(message)