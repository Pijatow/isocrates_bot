import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# --- Telegram Bot Configuration ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set!")

# --- Admin Configuration ---
# This is the chat ID of the admin or group where receipts will be sent.
# You can get this by talking to @userinfobot on Telegram.
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
if not ADMIN_CHAT_ID:
    raise ValueError("ADMIN_CHAT_ID environment variable not set!")


# --- Event Simulation ---
# Set this to True for a paid event, False for a free event.
EVENT_IS_PAID = True

PAYMENT_DETAILS = (
    "To complete your registration, please make a payment of **$10.00** to the following account:\n\n"
    "**Bank:** Isocrates Bank\n"
    "**Account Number:** 123-456-789\n\n"
    "After payment, please upload a clear photo or screenshot of your receipt."
)

# --- Conversation States ---
CHOOSING, AWAITING_RECEIPT = range(2)

# --- Network Configuration ---
# Global timeouts for Telegram API requests (in seconds)
CONNECT_TIMEOUT = 10
READ_TIMEOUT = 20

# Retry settings for network-related errors
MAX_RETRIES = 3
RETRY_DELAY = 2  # Initial delay in seconds, will be doubled each retry
