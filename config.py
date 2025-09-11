import os
from dotenv import load_dotenv

load_dotenv()

# --- Telegram Bot Configuration ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BOT_USERNAME = os.getenv("BOT_USERNAME")
if not TELEGRAM_BOT_TOKEN or not BOT_USERNAME:
    raise ValueError("TELEGRAM_BOT_TOKEN and BOT_USERNAME must be set in .env file!")

# --- Admin Configuration ---
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
admin_ids_str = os.getenv("ADMIN_USER_IDS", "")
ADMIN_USER_IDS = [int(uid.strip()) for uid in admin_ids_str.split(",") if uid.strip()]
if not ADMIN_CHAT_ID or not ADMIN_USER_IDS:
    raise ValueError("ADMIN_CHAT_ID and ADMIN_USER_IDS must be set in .env file!")

# --- Database Configuration ---
DATABASE_NAME = "isocrates.db"

# --- Conversation States ---
# User Flow
CHOOSING, AWAITING_DISCOUNT_PROMPT, AWAITING_DISCOUNT_CODE, AWAITING_RECEIPT = range(4)

# Admin Flow
(
    ADMIN_CHOOSING,
    MANAGING_EVENTS,
    VIEWING_EVENT,
    # Event Creation
    GETTING_EVENT_NAME,
    GETTING_EVENT_DESC,
    GETTING_EVENT_DATE,
    GETTING_EVENT_FEE,
    GETTING_EVENT_IS_PAID,
    GETTING_PAYMENT_DETAILS,
    GETTING_REMINDERS,
    # Discount Management
    MANAGING_DISCOUNTS,
    DELETING_DISCOUNT,
    GETTING_DISCOUNT_CODE,
    GETTING_DISCOUNT_TYPE,
    GETTING_DISCOUNT_VALUE,
    GETTING_DISCOUNT_USES,
) = range(4, 20)


# --- Network Configuration ---
CONNECT_TIMEOUT = 10
READ_TIMEOUT = 20
MAX_RETRIES = 3
RETRY_DELAY = 2

# --- Watchdog Configuration ---
BOT_RESTART_DELAY = 15  # Seconds watchdog waits before restarting the bot process
HEARTBEAT_INTERVAL = 15  # How often the bot writes its "I'm alive" signal
HEARTBEAT_TIMEOUT = (
    60  # How long watchdog waits for a heartbeat before declaring the bot frozen
)
