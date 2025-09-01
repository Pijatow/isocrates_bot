import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# --- Telegram Bot Configuration ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set!")

# --- Conversation States ---
CHOOSING, REGISTERING = range(2)

# --- Network Configuration ---
# Global timeouts for Telegram API requests (in seconds)
CONNECT_TIMEOUT = 10
READ_TIMEOUT = 20

# Retry settings for network-related errors
MAX_RETRIES = 3
RETRY_DELAY = 2  # Initial delay in seconds, will be doubled each retry
