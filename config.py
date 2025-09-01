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

# --- Event Configuration ---
# This is now a placeholder; actual event fees will be managed in the database.
EVENT_IS_PAID = True
PAYMENT_DETAILS = (
    "To complete your registration, please make a payment of $10.00 to:\n\n"
    "Bank: Isocrates Bank\n"
    "Account: 123-456-789\n\n"
    "After payment, please upload a clear photo of your receipt."
)

# --- Conversation States ---
# User Flow
CHOOSING, AWAITING_RECEIPT = range(2)

# Admin Flow
(
    ADMIN_CHOOSING,
    MANAGING_EVENTS,
    VIEWING_EVENT,  # New state for the detailed event view
    GETTING_EVENT_NAME,
    GETTING_EVENT_DATE,
    GETTING_REMINDERS,
) = range(2, 8)


# --- Network Configuration ---
CONNECT_TIMEOUT = 10
READ_TIMEOUT = 20
MAX_RETRIES = 3
RETRY_DELAY = 2
