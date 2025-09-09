import os
import logging
from bot.core import run_bot
from logging_config import setup_loggers
from database import initialize_database

# --- Proxy Settings (Optional) ---
# To run the bot through a proxy, uncomment the following lines.
os.environ["http_proxy"] = "http://127.0.0.1:10808"
os.environ["https_proxy"] = "http://127.0.0.1:10808"


if __name__ == "__main__":
    """
    This is the main entry point of the application.
    It orchestrates the setup of logging, the database, and then runs the bot.
    """
    setup_loggers()

    if "http_proxy" in os.environ or "https_proxy" in os.environ:
        logging.info(
            f"Using proxy settings: HTTP='{os.environ.get('http_proxy')}', HTTPS='{os.environ.get('https_proxy')}'"
        )

    initialize_database()

    logging.info("Starting Isocrates Bot...")
    run_bot()
    logging.info("Isocrates Bot has been shut down.")
