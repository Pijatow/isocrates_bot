import asyncio
import logging
from functools import wraps
from telegram import User
from telegram.error import NetworkError, TimedOut
from config import MAX_RETRIES, RETRY_DELAY, ADMIN_USER_IDS

network_logger = logging.getLogger("network")
interactions_logger = logging.getLogger("interactions")


def get_user_info(user: User) -> str:
    """Formats user information into a standardized string for logging."""
    if not user:
        return "User [Unknown]"

    parts = [f"ID:{user.id}"]
    if user.username:
        parts.append(f"UNAME:{user.username}")
    if user.full_name:
        safe_name = user.full_name.replace("'", "")
        parts.append(f"NAME:'{safe_name}'")

    return f"User [{', '.join(parts)}]"


def format_toman(amount: float) -> str:
    """Formats a number as a Toman currency string."""
    if amount == 0:
        return "Free"
    return f"{int(amount):,} Toman"


def admin_only(func):
    """
    A decorator to restrict access to a handler to only authorized admin users.
    """

    @wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        user = update.effective_user
        if user and user.id in ADMIN_USER_IDS:
            return await func(update, context, *args, **kwargs)
        else:
            interactions_logger.warning(
                f"UNAUTHORIZED access to '{func.__name__}' by {get_user_info(user)}."
            )
            if update.callback_query:
                await update.callback_query.answer(
                    "You are not authorized to perform this action.", show_alert=True
                )
            elif update.message:
                await update.message.reply_text(
                    "Sorry, this command is for admins only."
                )

    return wrapper


def retry_on_network_error(func):
    """
    A decorator to automatically retry a function on Telegram network errors.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        for attempt in range(MAX_RETRIES):
            try:
                return await func(*args, **kwargs)
            except (NetworkError, TimedOut) as e:
                if attempt + 1 == MAX_RETRIES:
                    network_logger.critical(
                        f"Function '{func.__name__}' failed after {MAX_RETRIES} attempts due to network error: {e}",
                        exc_info=True,
                    )
                    raise

                delay = RETRY_DELAY * (2**attempt)
                network_logger.warning(
                    f"Network error in '{func.__name__}': {e}. Retrying in {delay:.2f} seconds... (Attempt {attempt + 1}/{MAX_RETRIES})"
                )
                await asyncio.sleep(delay)

    return wrapper
