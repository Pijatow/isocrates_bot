import asyncio
import logging
from functools import wraps
from telegram.error import NetworkError, TimedOut

from config import MAX_RETRIES, RETRY_DELAY

# Get the root logger
logger = logging.getLogger()


def retry_on_network_error(func):
    """
    A decorator to automatically retry a function on Telegram network errors.
    Implements an exponential backoff strategy.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        for attempt in range(MAX_RETRIES):
            try:
                return await func(*args, **kwargs)
            except (NetworkError, TimedOut) as e:
                if attempt + 1 == MAX_RETRIES:
                    logger.critical(
                        f"Function '{func.__name__}' failed after {MAX_RETRIES} attempts due to network error: {e}",
                        exc_info=True,
                    )
                    raise

                delay = RETRY_DELAY * (2**attempt)
                logger.warning(
                    f"Network error in '{func.__name__}': {e}. Retrying in {delay:.2f} seconds... (Attempt {attempt + 1}/{MAX_RETRIES})"
                )
                await asyncio.sleep(delay)

    return wrapper
