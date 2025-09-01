from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Starts the conversation and asks the user if they want to register for the event.
    This is the entry point for the main conversation.
    """
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


async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the user's decision to register or not.
    This is where we will later add logic for paid vs. free events.
    """
    user_choice = update.message.text

    if user_choice == "Yes, Register Me!":
        # Placeholder for the real registration logic
        await update.message.reply_text(
            "Great! You are now registered. (Simple logic for now).",
            reply_markup=ReplyKeyboardRemove(),
        )
        # End the conversation
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "No problem. Hope to see you next time!", reply_markup=ReplyKeyboardRemove()
        )
        # End the conversation
        return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Cancels and ends the current conversation.
    Provides a way for the user to exit the registration flow at any time.
    """

    await update.message.reply_text(
        "Registration cancelled.", reply_markup=ReplyKeyboardRemove()
    )

    # End the conversation
    return ConversationHandler.END
