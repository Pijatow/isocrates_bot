import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, filters
import database as db
from .utils import retry_on_network_error
from config import (
    EVENT_IS_PAID,
    AWAITING_RECEIPT,
    ADMIN_CHAT_ID,
    CHOOSING,
    BOT_USERNAME,
    ADMIN_USER_IDS,
)

logger = logging.getLogger("UserMessages")
app_logger = logging.getLogger()


@retry_on_network_error
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Starts the conversation, saves user info, and handles referral links.
    """
    user = update.effective_user
    logger.info(f"User {user.id} ({user.username}) started the bot.")

    # Find inviter if a referral code is used
    inviter_id = None
    if context.args:
        referral_code = context.args[0]
        inviter_id = db.find_user_by_referral_code(referral_code)
        if inviter_id:
            logger.info(f"Referral successful: {user.id} was invited by {inviter_id}")

    # Add or update the user in the database, including who invited them
    db.add_or_update_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        invited_by=inviter_id,
    )

    active_event = db.get_active_event()
    if not active_event:
        await update.message.reply_text(
            "There are no active events open for registration right now. Please check back later!"
        )
        return ConversationHandler.END

    # Correctly access the event name by key
    event_name = active_event["name"]
    reply_keyboard = [["Yes, Register Me!", "No, thanks."]]
    await update.message.reply_text(
        f"Welcome to the Isocrates event bot!\n\n"
        f"The event '{event_name}' is now open for registration. Would you like to sign up?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return CHOOSING


@retry_on_network_error
async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the registration choice and creates a database record for the active event.
    """
    user = update.effective_user
    user_choice = update.message.text
    logger.info(f"User {user.id} chose: '{user_choice}'.")

    if user_choice == "No, thanks.":
        await update.message.reply_text(
            "No problem. Hope to see you next time!", reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    active_event = db.get_active_event()
    if not active_event:
        await update.message.reply_text(
            "Sorry, the event registration just closed. Please check back later."
        )
        return ConversationHandler.END

    # Correctly access the event ID by key
    event_id = active_event["event_id"]

    if EVENT_IS_PAID:
        db.create_registration(
            user_id=user.id, event_id=event_id, status="pending_verification"
        )
        await update.message.reply_text(
            "To complete your registration, please make a payment of $10.00 to:\n\n"
            "Bank: Isocrates Bank\n"
            "Account: 123-456-789\n\n"
            "After payment, please upload a clear photo of your receipt.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return AWAITING_RECEIPT
    else:
        db.create_registration(user_id=user.id, event_id=event_id, status="confirmed")
        await update.message.reply_text(
            "Great! You are now registered for this free event. See you there!",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END


@retry_on_network_error
async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the receipt, updates the database record for the active event, and forwards to admin."""
    user = update.effective_user
    photo = update.message.photo[-1]
    logger.info(f"User {user.id} submitted a receipt (file_id: {photo.file_id}).")

    active_event = db.get_active_event()
    if not active_event:
        await update.message.reply_text(
            "Sorry, we can't accept this receipt as the event registration is closed."
        )
        return ConversationHandler.END

    # Correctly access event details by key
    event_id = active_event["event_id"]
    event_name = active_event["name"]
    db.add_receipt_to_registration(
        user_id=user.id, event_id=event_id, receipt_file_id=photo.file_id
    )

    caption = (
        f"New payment receipt for event: '{event_name}'\n"
        f"From user: {user.full_name} (@{user.username})\n"
        f"User ID: {user.id}"
    )
    await context.bot.send_photo(
        chat_id=ADMIN_CHAT_ID, photo=photo.file_id, caption=caption
    )
    app_logger.info(
        f"Receipt from user {user.id} for event {event_id} forwarded to admin."
    )

    await update.message.reply_text(
        "Thank you! Your receipt has been submitted for verification.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


# --- Unchanged Handlers ---


@retry_on_network_error
async def my_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the user's unique referral link and their referral count."""
    user = update.effective_user
    referral_info = db.get_user_referral_info(user.id)
    if referral_info:
        referral_code, referral_count = referral_info
        referral_link = f"https://t.me/{BOT_USERNAME}?start={referral_code}"
        await update.message.reply_text(
            f"Your personal invitation link is:\n{referral_link}\n\n"
            f"Share this link with your friends. You have successfully invited {referral_count} people so far!"
        )
    else:
        await update.message.reply_text("Could not retrieve your referral information.")


@retry_on_network_error
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays a versatile help message for users and admins."""
    user = update.effective_user
    user_help_text = (
        "Here are the available commands:\n\n"
        "/start - Begins the registration process for the next event.\n"
        "/myreferral - Get your unique link to invite friends.\n"
        "/cancel - Stops any active process, like registration.\n"
        "/help - Shows this help message."
    )
    admin_help_text = (
        "--- ADMIN HELP ---\n"
        "You have access to all user commands plus the following:\n\n"
        "/admin - Opens the main admin control panel.\n"
        "  • From the panel, you can view pending registrations and manage events."
    )
    if user.id in ADMIN_USER_IDS:
        full_help_text = user_help_text + "\n\n" + admin_help_text
        await update.message.reply_text(full_help_text)
    else:
        await update.message.reply_text(user_help_text)


@retry_on_network_error
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the conversation."""
    user = update.effective_user
    logger.info(f"User {user.id} cancelled the conversation.")
    await update.message.reply_text(
        "Registration cancelled.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END
