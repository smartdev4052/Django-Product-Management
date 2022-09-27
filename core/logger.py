# import the logging library
import logging
logger = logging.getLogger(__name__)


def trigger_error(msg):
    logger.error(msg)


def trigger_warning(msg):
    logger.warning(msg)


def trigger_info(msg, prefix=''):
    logger.info(msg)
