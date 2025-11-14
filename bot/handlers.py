import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
import database as db
from .utils import retry_on_network_error, format_toman, get_user_info
from config import *

interactions_logger = logging.getLogger("interactions")
app_logger = logging.getLogger("app")


@retry_on_network_error
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    interactions_logger.info(f"{get_user_info(user)} started with command: /start")

    db.add_or_update_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        invited_by=None,
    )

    active_event = db.get_active_event()
    if not active_event:
        await update.message.reply_text(
            "There are no active events for registration right now."
        )
        return ConversationHandler.END

    context.user_data["active_event"] = dict(active_event)

    existing_registration = db.get_user_registration_for_event(
        user.id, active_event["event_id"]
    )
    if existing_registration:
        status = existing_registration["status"]
        if status == "confirmed":
            ticket = existing_registration["ticket_code"]
            await update.message.reply_text(
                f"You are already registered for '{active_event['name']}'! Your ticket code is: {ticket}"
            )
        elif status == "pending_verification":
            await update.message.reply_text(
                "You have already submitted a payment for this event. Please wait for an admin to approve it."
            )
        elif status == "rejected":
            await update.message.reply_text(
                "Your previous registration for this event was rejected. Please contact an admin if you believe this was a mistake."
            )
        return ConversationHandler.END

    # Show event details
    await update.message.reply_text(
        f"Welcome to the Isocrates event bot!\n\n"
        f"Event: {active_event['name']}\n\n"
        f"{active_event['description']}\n\n"
        f"Date: {active_event['date']}",
        reply_markup=ReplyKeyboardRemove(),
    )

    # If it's a free event, register immediately
    if not active_event["is_paid"]:
        db.create_registration(
            user_id=user.id,
            event_id=active_event["event_id"],
            status="pending",
            final_fee=0.0,
        )
        reg_id = db.get_last_registration_id(user.id, active_event["event_id"])
        if reg_id:
            ticket_code = db.update_registration_status(reg_id, "confirmed")
            await update.message.reply_text(
                "Great! You are now registered for this free event. See you there!\n\n"
                f"Your ticket code is: {ticket_code}"
            )
        return ConversationHandler.END

    # For paid events, check if there are any active discount codes
    discount_codes = db.get_discount_codes_for_event(active_event["event_id"])
    active_discounts = [code for code in discount_codes if code["is_active"] and code["uses_left"] > 0]

    if active_discounts:
        # Ask about discount code only if there are active codes
        reply_keyboard = [["Yes", "No"]]
        await update.message.reply_text(
            "Do you have a discount code?",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, resize_keyboard=True
            ),
        )
        return AWAITING_DISCOUNT_PROMPT
    else:
        # No discount codes available, proceed directly to payment
        context.user_data["final_fee"] = active_event["fee"]
        context.user_data["discount_code"] = None

        final_fee_str = format_toman(active_event["fee"])
        payment_details = active_event["payment_details"]

        instruction_line = "\n\nپس از پرداخت، لطفا از رسید خود عکس واضحی ارسال کنید."
        message = (
            f"مبلغ قابل پرداخت: {final_fee_str}\n\n{payment_details}{instruction_line}"
        )

        await update.message.reply_text(message)
        return AWAITING_RECEIPT





@retry_on_network_error
async def handle_discount_prompt(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    user = update.effective_user
    user_choice = update.message.text
    interactions_logger.info(
        f"{get_user_info(user)} responded to discount prompt with: '{user_choice}'."
    )
    active_event = context.user_data.get("active_event")

    if user_choice == "Yes":
        await update.message.reply_text(
            "Please enter your discount code:", reply_markup=ReplyKeyboardRemove()
        )
        return AWAITING_DISCOUNT_CODE
    else:
        context.user_data["final_fee"] = active_event["fee"]
        context.user_data["discount_code"] = None

        final_fee_str = format_toman(active_event["fee"])
        payment_details = active_event["payment_details"]

        instruction_line = "\n\nپس از پرداخت، لطفا از رسید خود عکس واضحی ارسال کنید."
        message = (
            f"مبلغ قابل پرداخت: {final_fee_str}\n\n{payment_details}{instruction_line}"
        )

        await update.message.reply_text(message, reply_markup=ReplyKeyboardRemove())
        return AWAITING_RECEIPT


@retry_on_network_error
async def handle_discount_code(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    code = update.message.text.upper()
    user = update.effective_user
    interactions_logger.info(
        f"{get_user_info(user)} submitted discount code: '{code}'."
    )
    active_event = context.user_data.get("active_event")

    discount = db.get_discount_code(active_event["event_id"], code)

    if not discount:
        await update.message.reply_text(
            "That code is invalid, has expired, or does not belong to this event. Please try again or type /cancel."
        )
        return AWAITING_DISCOUNT_CODE

    original_fee = active_event["fee"]
    final_fee = original_fee

    if discount["discount_type"] == "percentage":
        final_fee = original_fee * (1 - discount["value"] / 100)
    elif discount["discount_type"] == "fixed":
        final_fee = original_fee - discount["value"]

    final_fee = max(0, final_fee)

    context.user_data["final_fee"] = final_fee
    context.user_data["discount_code"] = code
    context.user_data["discount_code_id"] = discount["code_id"]

    if final_fee <= 0:
        db.create_registration(
            user_id=user.id,
            event_id=active_event["event_id"],
            status="pending",
            final_fee=0.0,
            discount_code=code,
        )
        db.use_discount_code(discount["code_id"])
        reg_id = db.get_last_registration_id(user.id, active_event["event_id"])
        if reg_id:
            ticket_code = db.update_registration_status(reg_id, "confirmed")
            await update.message.reply_text(
                "✅ Your 100% discount code has been successfully applied!\n\n"
                "You are now registered for this event. See you there!\n\n"
                f"Your ticket code is: {ticket_code}",
                reply_markup=ReplyKeyboardRemove(),
            )
        return ConversationHandler.END

    final_fee_str = format_toman(final_fee)
    payment_details = active_event["payment_details"]

    instruction_line = "\n\nپس از پرداخت، لطفا از رسید خود عکس واضحی ارسال کنید."
    message = f"✅ Discount applied!\n\nمبلغ قابل پرداخت: {final_fee_str}\n\n{payment_details}{instruction_line}"

    await update.message.reply_text(message, reply_markup=ReplyKeyboardRemove())
    return AWAITING_RECEIPT


@retry_on_network_error
async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    photo = update.message.photo[-1]
    active_event = context.user_data.get("active_event")
    final_fee = context.user_data.get("final_fee")
    discount_code = context.user_data.get("discount_code")

    interactions_logger.info(
        f"{get_user_info(user)} submitted a receipt photo [FileID:{photo.file_id}]."
    )

    db.create_registration(
        user_id=user.id,
        event_id=active_event["event_id"],
        status="pending_verification",
        final_fee=final_fee,
        discount_code=discount_code,
    )
    db.add_receipt_to_registration(
        user_id=user.id,
        event_id=active_event["event_id"],
        receipt_file_id=photo.file_id,
    )

    if "discount_code_id" in context.user_data:
        db.use_discount_code(context.user_data["discount_code_id"])

    # Send photo with details to admin chat
    caption = (
        f"New payment receipt for: '{active_event['name']}'\n"
        f"From User: {get_user_info(user)}\n"
        f"Fee Paid: {format_toman(final_fee)}\n"
        f"Discount Used: {discount_code or 'None'}"
    )
    await context.bot.send_photo(
        chat_id=ADMIN_CHAT_ID, photo=photo.file_id, caption=caption
    )

    # Send a separate, simple text notification for high visibility
    notification_text = f"📢 New receipt from {user.full_name} (@{user.username}) requires verification."
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=notification_text)

    await update.message.reply_text(
        "Thank you! Your receipt has been submitted for verification.",
        reply_markup=ReplyKeyboardRemove(),
    )
    context.user_data.clear()
    return ConversationHandler.END


@retry_on_network_error
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    interactions_logger.info(f"{get_user_info(user)} requested /help.")
    user_help_text = (
        "Here are the available commands:\n\n"
        "/start - Register for the active event.\n"
        "/cancel - Stop any active process, like registration.\n"
        "/help - Shows this help message."
    )
    admin_help_text = (
        "\n\n--- 👑 ADMIN HELP ---\n"
        "You have access to all user commands plus:\n\n"
        "/admin - Open the main admin control panel."
    )

    if user.id in ADMIN_USER_IDS:
        full_help_text = user_help_text + admin_help_text
        await update.message.reply_text(full_help_text)
    else:
        await update.message.reply_text(user_help_text)


@retry_on_network_error
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    interactions_logger.info(
        f"{get_user_info(user)} cancelled the conversation with /cancel."
    )
    await update.message.reply_text(
        "Action cancelled.", reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    return ConversationHandler.END
