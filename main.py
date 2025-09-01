import os
import logging
from bot.core import run_bot
from logging_config import setup_loggers
from database import init_db

# --- Proxy Settings (Optional) ---
os.environ["http_proxy"] = "http://127.0.0.1:10808"
os.environ["https_proxy"] = "http://127.0.0.1:10808"


if __name__ == "__main__":
    """
    Main entry point: sets up logging, initializes the DB, and runs the bot.
    """
    setup_loggers()

    if "http_proxy" in os.environ or "https_proxy" in os.environ:
        logging.info(
            f"Using proxy: HTTP='{os.environ.get('http_proxy')}', HTTPS='{os.environ.get('https_proxy')}'"
        )

    # --- Initialize the database ---
    init_db()

    logging.info("Starting Isocrates Bot...")
    run_bot()
    logging.info("Isocrates Bot has been shut down.")
