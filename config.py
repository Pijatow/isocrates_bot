import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# It's highly recommended to use environment variables for sensitive data.
# Create a file named ".env" in the root of your project and add:
# TELEGRAM_BOT_TOKEN="YOUR_REAL_TOKEN_HERE"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set!")

# Conversation states
CHOOSING, REGISTERING = range(2)
