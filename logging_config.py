import logging
import os
from logging.handlers import RotatingFileHandler

# --- Basic Setup ---
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)


# --- Custom Filter to Reduce Noise ---
class NoisyLibrariesFilter(logging.Filter):
    """
    Filters out noisy INFO-level logs from libraries that we don't need to see
    during normal operation, like the constant "Application started/stopped" messages.
    """

    def filter(self, record):
        # We only want to suppress INFO level logs from these specific sources
        is_noisy_source = record.name.startswith(("telegram.ext", "apscheduler"))
        is_info_level = record.levelno == logging.INFO

        return not (is_noisy_source and is_info_level)


# --- Formatters ---
# A more concise format for the console
console_formatter = logging.Formatter(
    "%(asctime)s - %(levelname)-8s - %(name)s - %(message)s"
)
file_formatter = logging.Formatter(
    "%(asctime)s - %(levelname)-8s - %(name)s - %(message)s [in %(pathname)s:%(lineno)d]"
)

# --- Handlers ---
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(console_formatter)
console_handler.addFilter(NoisyLibrariesFilter())  # Add the filter here

# General application log (startup, shutdown, major events)
app_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, "app.log"), maxBytes=5 * 1024 * 1024, backupCount=2
)
app_handler.setLevel(logging.INFO)
app_handler.setFormatter(file_formatter)
app_handler.addFilter(NoisyLibrariesFilter())  # And also here

# Log for all user and admin interactions
interactions_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, "interactions.log"), maxBytes=5 * 1024 * 1024, backupCount=2
)
interactions_handler.setLevel(logging.INFO)
interactions_handler.setFormatter(file_formatter)

# Log for network-related events (timeouts, retries, etc.)
network_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, "network.log"), maxBytes=5 * 1024 * 1024, backupCount=2
)
network_handler.setLevel(logging.INFO)
network_handler.setFormatter(file_formatter)

# Log for scheduler jobs (checking for reminders)
scheduler_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, "scheduler.log"), maxBytes=5 * 1024 * 1024, backupCount=2
)
scheduler_handler.setLevel(logging.DEBUG)
scheduler_handler.setFormatter(file_formatter)


# --- Main Setup Function ---
def setup_loggers():
    """Sets up and configures all the loggers for the application."""
    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = [console_handler, app_handler]

    # --- Configure Specialized Loggers ---
    # Interactions logger
    interactions_logger = logging.getLogger("interactions")
    interactions_logger.setLevel(logging.INFO)
    interactions_logger.addHandler(interactions_handler)
    interactions_logger.propagate = False  # Don't send these to the root logger

    # Network logger
    network_logger = logging.getLogger("network")
    network_logger.setLevel(logging.INFO)
    network_logger.addHandler(network_handler)
    network_logger.propagate = False

    # Scheduler logger
    scheduler_logger = logging.getLogger("scheduler")
    scheduler_logger.setLevel(logging.DEBUG)
    scheduler_logger.addHandler(scheduler_handler)
    scheduler_logger.propagate = False

    logging.info("Logging configuration loaded successfully.")
