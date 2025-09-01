import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)
import database as db
from .utils import admin_only
from config import (
    MANAGING_EVENTS,
    GETTING_EVENT_NAME,
    GETTING_EVENT_DATE,
    GETTING_REMINDERS,
    ADMIN_CHOOSING,
)


logger = logging.getLogger()


@admin_only
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for the admin conversation. Shows the main admin panel."""
    # This can be called by a command or by a "back" button, so we handle both.
    message = update.message or update.callback_query.message

    keyboard = [
        [
            InlineKeyboardButton(
                "View Pending Registrations", callback_data="view_pending"
            )
        ],
        [InlineKeyboardButton("Manage Events", callback_data="manage_events")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # If it's a callback, edit the message. If it's a command, send a new one.
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "Admin Control Panel:", reply_markup=reply_markup
        )
    else:
        await message.reply_text("Admin Control Panel:", reply_markup=reply_markup)

    return ADMIN_CHOOSING


@admin_only
async def view_pending_registrations(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Displays the next pending registration for approval."""
    query = update.callback_query
    await query.answer()

    pending_reg = db.get_next_pending_registration()

    if not pending_reg:
        await query.edit_message_text(text="No pending registrations found.")
        return ConversationHandler.END

    reg_id, user_id, file_id, username, first_name, event_name = pending_reg
    caption = (
        f"Pending Registration for event: '{event_name}'\n"
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
    await query.message.reply_photo(
        photo=file_id, caption=caption, reply_markup=reply_markup
    )
    # The message with the buttons is the one showing the receipt, so we can't delete the query message.
    # Instead, we effectively end the interaction here from the admin's side.
    return ConversationHandler.END


@admin_only
async def handle_registration_approval(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handles the 'Approve' action from the admin."""
    query = update.callback_query
    await query.answer()
    _, reg_id, user_id = query.data.split("_")

    db.update_registration_status(int(reg_id), "confirmed")
    await query.edit_message_caption(caption=f"✅ Registration {reg_id} approved.")
    await context.bot.send_message(
        chat_id=user_id,
        text="Congratulations! Your registration has been approved. You are now confirmed for the event.",
    )


@admin_only
async def handle_registration_rejection(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handles the 'Reject' action from the admin."""
    query = update.callback_query
    await query.answer()
    _, reg_id, user_id = query.data.split("_")

    db.update_registration_status(int(reg_id), "rejected")
    await query.edit_message_caption(caption=f"❌ Registration {reg_id} rejected.")
    await context.bot.send_message(
        chat_id=user_id,
        text="Unfortunately, your registration could not be approved. Please contact an admin for details.",
    )


# --- Event Management Sub-Conversation ---


@admin_only
async def manage_events(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Shows the event management options with a list of all events."""
    query = update.callback_query
    await query.answer()

    events = db.get_all_events()
    keyboard = []

    if events:
        for event in events:
            prefix = "✅ " if event["is_active"] else ""
            button_text = f"{prefix}{event['name']} ({event['date']})"
            # We will add functionality for this button later
            keyboard.append(
                [
                    InlineKeyboardButton(
                        button_text, callback_data=f"event_{event['event_id']}"
                    )
                ]
            )

    keyboard.append(
        [InlineKeyboardButton("➕ Create New Event", callback_data="create_event")]
    )
    keyboard.append(
        [InlineKeyboardButton("⬅️ Back to Admin Panel", callback_data="admin_back")]
    )

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Event Management:", reply_markup=reply_markup)
    return MANAGING_EVENTS


@admin_only
async def prompt_for_event_name(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Asks the admin for the new event's name."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Please enter the name for the new event:")
    return GETTING_EVENT_NAME


@admin_only
async def get_event_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Saves the event name and asks for the date."""
    context.user_data["event_name"] = update.message.text
    await update.message.reply_text(
        "Great. Now, please enter the event date and time in YYYY-MM-DD HH:MM format:"
    )
    return GETTING_EVENT_DATE


@admin_only
async def get_event_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Saves the event date and asks for reminder times."""
    context.user_data["event_date"] = update.message.text
    await update.message.reply_text(
        "Enter the reminder schedule as comma-separated hours before the event (e.g., 24, 1):"
    )
    return GETTING_REMINDERS


@admin_only
async def save_event_and_finish(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Saves the new event to the database and ends the admin conversation."""
    reminders = update.message.text
    event_name = context.user_data.get("event_name")
    event_date = context.user_data.get("event_date")

    if not event_name or not event_date:
        await update.message.reply_text("Something went wrong. Please start over.")
        context.user_data.clear()
        return ConversationHandler.END

    db.create_event(name=event_name, date=event_date, reminders=reminders)

    await update.message.reply_text(
        f"✅ New event '{event_name}' created and set as active."
    )
    context.user_data.clear()

    # Restart the admin panel to show the updated event list
    await admin_panel(update, context)
    return ConversationHandler.END


@admin_only
async def cancel_admin_conversation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Cancels any admin action and clears temporary data."""
    # Determine if it's a command or a callback query
    if update.callback_query:
        await update.callback_query.answer()
        message = update.callback_query.message
        await message.edit_text("Admin action cancelled.")
    else:
        message = update.message
        await message.reply_text("Admin action cancelled.")

    context.user_data.clear()
    return ConversationHandler.END
