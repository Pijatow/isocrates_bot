import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, filters
import database as db
from .utils import retry_on_network_error
from config import EVENT_IS_PAID, AWAITING_RECEIPT, ADMIN_CHAT_ID, CHOOSING

logger = logging.getLogger("UserMessages")
app_logger = logging.getLogger()


@retry_on_network_error
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Starts the conversation and saves/updates user info in the database.
    """
    user = update.effective_user
    logger.info(f"User {user.id} ({user.username}) started the bot.")

    # Add or update the user in the database
    db.add_or_update_user(
        user_id=user.id, username=user.username, first_name=user.first_name
    )

    reply_keyboard = [["Yes, Register Me!", "No, thanks."]]
    await update.message.reply_text(
        "Welcome to the Isocrates event bot!\n\n"
        "This weekend's event is now open for registration. Would you like to sign up?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return CHOOSING


@retry_on_network_error
async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the registration choice and creates a database record accordingly.
    """
    user = update.effective_user
    user_choice = update.message.text
    logger.info(f"User {user.id} chose: '{user_choice}'.")

    if user_choice == "No, thanks.":
        await update.message.reply_text(
            "No problem. Hope to see you next time!", reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    if EVENT_IS_PAID:
        db.create_registration(user_id=user.id, status="pending_verification")
        await update.message.reply_text(
            "To complete your registration, please make a payment of $10.00 to:\n\n"
            "Bank: Isocrates Bank\n"
            "Account: 123-456-789\n\n"
            "After payment, please upload a clear photo of your receipt.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return AWAITING_RECEIPT
    else:
        db.create_registration(user_id=user.id, status="confirmed")
        await update.message.reply_text(
            "Great! You are now registered for this free event. See you there!",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END


@retry_on_network_error
async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the receipt, saves the file ID to the database, and forwards to admin.
    """
    user = update.effective_user
    photo = update.message.photo[-1]
    logger.info(f"User {user.id} submitted a receipt (file_id: {photo.file_id}).")

    # Update the registration record with the receipt file ID
    db.create_registration(
        user_id=user.id, status="pending_verification", receipt_file_id=photo.file_id
    )

    caption = (
        f"New payment receipt from user: {user.full_name}\n"
        f"Username: @{user.username}\n"
        f"User ID: {user.id}\n\n"
        "Please verify and approve their registration."
    )
    await context.bot.send_photo(
        chat_id=ADMIN_CHAT_ID, photo=photo.file_id, caption=caption
    )
    app_logger.info(f"Receipt from user {user.id} forwarded to admin.")

    await update.message.reply_text(
        "Thank you! We have received your receipt.\n"
        "An admin will verify it shortly. You will receive a confirmation message once approved.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


@retry_on_network_error
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Cancels the conversation.
    """
    user = update.effective_user
    logger.info(f"User {user.id} cancelled the conversation.")
    await update.message.reply_text(
        "Registration cancelled.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END
