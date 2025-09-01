import os
import logging
from bot.core import run_bot
from logging_config import setup_loggers

# --- Proxy Settings ---
# To run the bot through a proxy, uncomment the following lines and ensure your
# proxy server is running at the specified address. This should be one of the
# very first things the application does to catch all network requests.
#
os.environ["http_proxy"] = "http://127.0.0.1:10808"
os.environ["https_proxy"] = "http://127.0.0.1:10808"


if __name__ == "__main__":
    """
    This is the main entry point of the application.
    It sets up logging and then calls the function to run the bot.
    """
    # Apply the logging configuration
    setup_loggers()

    # Log a confirmation message if proxy settings are active
    if "http_proxy" in os.environ or "https_proxy" in os.environ:
        logging.info(
            f"Using proxy settings: HTTP='{os.environ.get('http_proxy')}', HTTPS='{os.environ.get('https_proxy')}'"
        )

    logging.info("Starting Isocrates Bot...")
    run_bot()
    logging.info("Isocrates Bot has been shut down.")
