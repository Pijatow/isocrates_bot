import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# --- Telegram Bot Configuration ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set!")

# --- Admin Configuration ---
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
if not ADMIN_CHAT_ID:
    raise ValueError("ADMIN_CHAT_ID environment variable not set!")

# --- Database Configuration ---
DATABASE_NAME = "isocrates.db"

# --- Event Simulation ---
EVENT_IS_PAID = True

# --- Conversation States ---
CHOOSING, AWAITING_RECEIPT = range(2)

# --- Network Configuration ---
CONNECT_TIMEOUT = 10
READ_TIMEOUT = 20
MAX_RETRIES = 3
RETRY_DELAY = 2
