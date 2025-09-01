import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database as db
from .utils import restricted_to_admins, retry_on_network_error

logger = logging.getLogger()


@retry_on_network_error
@restricted_to_admins
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the main admin control panel."""
    keyboard = [
        [
            InlineKeyboardButton(
                "View Pending Registrations", callback_data="view_pending"
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Admin Control Panel:", reply_markup=reply_markup)


@retry_on_network_error
@restricted_to_admins
async def view_pending_registrations(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Fetches and displays the next pending registration for admin review."""
    query = update.callback_query
    await query.answer()  # Acknowledge the button press

    pending_reg = db.get_next_pending_registration()

    if not pending_reg:
        await query.edit_message_text(text="No pending registrations found.")
        return

    reg_id, user_id, receipt_file_id, username, first_name = pending_reg

    # Store the registration ID in context for the approval/rejection handlers
    context.user_data["current_reg_id"] = reg_id
    context.user_data["current_user_id"] = user_id

    caption = (
        f"Pending Registration\n\n"
        f"User: {first_name} (@{username})\n"
        f"User ID: {user_id}\n"
        f"Registration ID: {reg_id}"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Approve", callback_data=f"approve_{reg_id}_{user_id}"
            ),
            InlineKeyboardButton(
                "❌ Reject", callback_data=f"reject_{reg_id}_{user_id}"
            ),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_photo(
        chat_id=query.message.chat_id,
        photo=receipt_file_id,
        caption=caption,
        reply_markup=reply_markup,
    )
    # Delete the "View Pending Registrations" button message
    await query.delete_message()


@retry_on_network_error
@restricted_to_admins
async def handle_registration_approval(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handles the 'Approve' button click from an admin."""
    query = update.callback_query
    await query.answer()

    # Data is in the format "approve_reg_id_user_id"
    _, reg_id, user_id = query.data.split("_")
    reg_id, user_id = int(reg_id), int(user_id)

    db.update_registration_status(reg_id, "confirmed")
    logger.info(f"Admin {update.effective_user.id} approved registration {reg_id}.")

    await query.edit_message_caption(caption=f"✅ Registration {reg_id} Approved.")

    # Notify the user
    await context.bot.send_message(
        chat_id=user_id,
        text="Congratulations! Your registration for the Isocrates event has been approved. Welcome aboard!",
    )


@retry_on_network_error
@restricted_to_admins
async def handle_registration_rejection(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handles the 'Reject' button click from an admin."""
    query = update.callback_query
    await query.answer()

    # Data is in the format "reject_reg_id_user_id"
    _, reg_id, user_id = query.data.split("_")
    reg_id, user_id = int(reg_id), int(user_id)

    db.update_registration_status(reg_id, "rejected")
    logger.warning(f"Admin {update.effective_user.id} rejected registration {reg_id}.")

    await query.edit_message_caption(caption=f"❌ Registration {reg_id} Rejected.")

    # Notify the user
    await context.bot.send_message(
        chat_id=user_id,
        text="We're sorry, but there was an issue with your registration and it has been rejected. Please contact support for assistance.",
    )
