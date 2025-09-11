import os
import logging
from bot.core import run_bot
from logging_config import setup_loggers
from database import initialize_database

# Optional: Proxy settings can still be configured here if needed.
os.environ["http_proxy"] = "http://127.0.0.1:10808"
os.environ["https_proxy"] = "http://127.0.0.1:10808"


if __name__ == "__main__":
    """
    This is the main entry point for the bot's execution process.
    It is launched and monitored by the main.py watchdog.
    If this script crashes, the watchdog will restart it.
    """
    setup_loggers()

    if "http_proxy" in os.environ or "https_proxy" in os.environ:
        logging.info(
            f"Using proxy settings: HTTP='{os.environ.get('http_proxy')}', HTTPS='{os.environ.get('https_proxy')}'"
        )

    initialize_database()

    try:
        logging.info("Starting Isocrates Bot process...")
        run_bot()
    except Exception as e:
        logging.critical(
            f"The bot has crashed unexpectedly in the core process: {e}", exc_info=True
        )
    finally:
        logging.info("Isocrates Bot process has been shut down.")
