import logging
import os
from logging.handlers import RotatingFileHandler

# --- Basic Setup ---
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# --- Formatters ---
console_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
file_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s [in %(pathname)s:%(lineno)d]"
)

# --- Handlers ---
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(console_formatter)

error_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, "errors.log"), maxBytes=5 * 1024 * 1024, backupCount=2
)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(file_formatter)

messages_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, "messages.log"), maxBytes=5 * 1024 * 1024, backupCount=2
)
messages_handler.setLevel(logging.INFO)
messages_handler.setFormatter(file_formatter)

app_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, "app.log"), maxBytes=5 * 1024 * 1024, backupCount=2
)
app_handler.setLevel(logging.DEBUG)
app_handler.setFormatter(file_formatter)


def setup_loggers():
    """Sets up and configures all the loggers for the application."""
    logging.basicConfig(
        level=logging.INFO, handlers=[console_handler, error_handler, app_handler]
    )

    messages_logger = logging.getLogger("UserMessages")
    messages_logger.setLevel(logging.INFO)
    messages_logger.addHandler(messages_handler)
    messages_logger.propagate = False

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.info("Logging configuration loaded successfully.")
