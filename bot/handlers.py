import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from .utils import retry_on_network_error

# Get the specific logger for user messages
logger = logging.getLogger("UserMessages")
# Get the root logger for general app logic
app_logger = logging.getLogger()


@retry_on_network_error
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Starts the conversation and asks the user if they want to register for the event.
    This is the entry point for the main conversation.
    """
    user = update.effective_user
    logger.info(f"User {user.id} ({user.username}) started the bot with /start.")

    # Define the keyboard buttons
    reply_keyboard = [["Yes, Register Me!", "No, thanks."]]

    await update.message.reply_text(
        "Welcome to the Isocrates event bot!\n\n"
        "This weekend's event is now open for registration. Would you like to sign up?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="Register for the event?",
        ),
    )

    # Transition to the CHOOSING state to wait for the user's reply
    from config import CHOOSING

    return CHOOSING


@retry_on_network_error
async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the user's decision to register or not.
    This is where we will later add logic for paid vs. free events.
    """
    user = update.effective_user
    user_choice = update.message.text
    logger.info(f"User {user.id} ({user.username}) made a choice: '{user_choice}'.")

    if user_choice == "Yes, Register Me!":
        # Placeholder for the real registration logic
        await update.message.reply_text(
            "Great! You are now registered. (Simple logic for now).",
            reply_markup=ReplyKeyboardRemove(),
        )
        app_logger.info(f"User {user.id} completed a registration (placeholder).")
        # End the conversation
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "No problem. Hope to see you next time!", reply_markup=ReplyKeyboardRemove()
        )
        # End the conversation
        return ConversationHandler.END


@retry_on_network_error
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Cancels and ends the current conversation.
    Provides a way for the user to exit the registration flow at any time.
    """
    user = update.effective_user
    logger.info(f"User {user.id} ({user.username}) cancelled the conversation.")

    await update.message.reply_text(
        "Registration cancelled.", reply_markup=ReplyKeyboardRemove()
    )

    # End the conversation
    return ConversationHandler.END
