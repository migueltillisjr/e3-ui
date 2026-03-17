import logging
import os
import pprint

import boto3


def set_logger(log_level: str = "INFO") -> object:
    log_level = os.environ.get("LOG_LEVEL", log_level).strip().upper()
    logging.basicConfig(format="[%(asctime)s] p%(process)s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s")
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    return logger

dir_current = os.path.abspath("")
logger = set_logger()


def set_pretty_printer():
    return pprint.PrettyPrinter(indent=2, width=100)