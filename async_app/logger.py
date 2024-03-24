import sys

from loguru import logger


def set_verbosity(ctx, option, log_level):
    logger.remove()
    if log_level == 1:
        logger.add(sys.stderr, level="INFO")
    elif log_level > 1:
        logger.add(sys.stderr, level="DEBUG")
