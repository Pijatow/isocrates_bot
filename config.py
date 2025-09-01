import os
from dotenv import load_dotenv

load_dotenv()

# --- Telegram Bot Configuration ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set!")

# The bot's username (without the '@') is needed for referral links
BOT_USERNAME = os.getenv("BOT_USERNAME")
if not BOT_USERNAME:
    raise ValueError("BOT_USERNAME environment variable not set!")

# --- Admin Configuration ---
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
if not ADMIN_CHAT_ID:
    raise ValueError("ADMIN_CHAT_ID environment variable not set!")

admin_ids_str = os.getenv("ADMIN_USER_IDS", "")
ADMIN_USER_IDS = [
    int(user_id.strip()) for user_id in admin_ids_str.split(",") if user_id.strip()
]
if not ADMIN_USER_IDS:
    raise ValueError("ADMIN_USER_IDS environment variable not set!")

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
