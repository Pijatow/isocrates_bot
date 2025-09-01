import asyncio
import logging
from functools import wraps
from telegram.error import NetworkError, TimedOut
from telegram import Update
from telegram.ext import ContextTypes

from config import MAX_RETRIES, RETRY_DELAY, ADMIN_USER_IDS

logger = logging.getLogger()


def restricted_to_admins(func):
    """
    Decorator to restrict access to a handler to only authorized admin users.
    """

    @wraps(func)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        user_id = update.effective_user.id
        if user_id not in ADMIN_USER_IDS:
            logger.warning(
                f"Unauthorized access attempt by user {user_id} to admin command '{func.__name__}'."
            )
            await update.message.reply_text(
                "You are not authorized to use this command."
            )
            return
        return await func(update, context, *args, **kwargs)

    return wrapper


def retry_on_network_error(func):
    """
    Decorator to automatically retry a function on Telegram network errors.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        for attempt in range(MAX_RETRIES):
            try:
                return await func(*args, **kwargs)
            except (NetworkError, TimedOut) as e:
                if attempt + 1 == MAX_RETRIES:
                    logger.critical(
                        f"Function '{func.__name__}' failed after {MAX_RETRIES} attempts: {e}",
                        exc_info=True,
                    )
                    raise
                delay = RETRY_DELAY * (2**attempt)
                logger.warning(
                    f"Network error in '{func.__name__}': {e}. Retrying in {delay:.2f}s... (Attempt {attempt + 1}/{MAX_RETRIES})"
                )
                await asyncio.sleep(delay)

    return wrapper
