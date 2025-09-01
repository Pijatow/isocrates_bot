import logging
from bot.core import run_bot
from logging_config import setup_loggers

if __name__ == "__main__":
    """
    This is the main entry point of the application.
    It sets up logging and then calls the function to run the bot.
    """
    # Apply the logging configuration
    setup_loggers()

    logging.info("Starting Isocrates Bot...")
    run_bot()
    logging.info("Isocrates Bot has been shut down.")
