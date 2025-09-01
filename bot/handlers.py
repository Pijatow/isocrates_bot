import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, ParseMode
from telegram.ext import ContextTypes, ConversationHandler, filters
from .utils import retry_on_network_error
from config import EVENT_IS_PAID, PAYMENT_DETAILS, AWAITING_RECEIPT, ADMIN_CHAT_ID

# Get the specific logger for user messages
logger = logging.getLogger("UserMessages")
# Get the root logger for general app logic
app_logger = logging.getLogger()


@retry_on_network_error
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Starts the conversation and asks the user if they want to register for the event.
    """
    user = update.effective_user
    logger.info(f"User {user.id} ({user.username}) started the bot with /start.")

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

    from config import CHOOSING

    return CHOOSING


@retry_on_network_error
async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the user's decision, branching between paid and free event flows.
    """
    user = update.effective_user
    user_choice = update.message.text
    logger.info(f"User {user.id} ({user.username}) chose: '{user_choice}'.")

    if user_choice == "No, thanks.":
        await update.message.reply_text(
            "No problem. Hope to see you next time!", reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    if EVENT_IS_PAID:
        # --- Paid Event Flow ---
        app_logger.info(f"Initiating paid registration flow for user {user.id}.")
        await update.message.reply_text(
            PAYMENT_DETAILS,
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return AWAITING_RECEIPT
    else:
        # --- Free Event Flow ---
        app_logger.info(f"Registering user {user.id} for a free event.")
        await update.message.reply_text(
            "Great! You are now registered for this free event. See you there!",
            reply_markup=ReplyKeyboardRemove(),
        )
        # Here you would add the user to the database as confirmed.
        return ConversationHandler.END


@retry_on_network_error
async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the user's uploaded payment receipt.
    Saves the photo and forwards it to the admin for verification.
    """
    user = update.effective_user
    photo = update.message.photo[-1]  # Get the highest resolution photo

    logger.info(f"User {user.id} ({user.username}) submitted a receipt.")

    # 1. Forward the receipt to the admin(s)
    caption = (
        f"New payment receipt from user: {user.full_name}\n"
        f"Username: @{user.username}\n"
        f"User ID: `{user.id}`\n\n"
        f"Please verify and approve their registration."
    )
    await context.bot.send_photo(
        chat_id=ADMIN_CHAT_ID,
        photo=photo.file_id,
        caption=caption,
        parse_mode=ParseMode.MARKDOWN_V2,
    )
    app_logger.info(
        f"Receipt from user {user.id} forwarded to admin chat {ADMIN_CHAT_ID}."
    )

    # 2. Confirm receipt with the user
    await update.message.reply_text(
        "Thank you! We have received your receipt.\n"
        "An admin will verify it shortly. You will receive a confirmation message once your registration is approved.",
        reply_markup=ReplyKeyboardRemove(),
    )

    # Here you would save the user's status as "pending_verification" in the database.

    return ConversationHandler.END


@retry_on_network_error
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Cancels and ends the current conversation.
    """
    user = update.effective_user
    logger.info(f"User {user.id} ({user.username}) cancelled the conversation.")

    await update.message.reply_text(
        "Registration cancelled.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END
