import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)
import database as db
from .utils import admin_only
from config import *

logger = logging.getLogger()


# --- Main Admin Panel ---
@admin_only
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for the admin conversation. Shows the main admin panel."""
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

    (
        reg_id,
        user_id,
        file_id,
        username,
        first_name,
        event_name,
        final_fee,
        discount_code,
    ) = pending_reg
    caption = (
        f"Pending Registration for: '{event_name}'\n"
        f"User: {first_name} (@{username})\n"
        f"User ID: {user_id}\n"
        f"Fee Paid: ${final_fee:.2f}\n"
        f"Discount Used: {discount_code or 'None'}"
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
        photo=file_id,
        caption=caption,
        reply_markup=reply_markup,
    )
    await query.delete_message()
    return ConversationHandler.END


@admin_only
async def handle_registration_approval(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handles the 'Approve' action from the admin."""
    query = update.callback_query
    await query.answer()
    _, reg_id, user_id = query.data.split("_")
    ticket_code = db.update_registration_status(int(reg_id), "confirmed")
    await query.edit_message_caption(caption=f"✅ Registration {reg_id} approved.")
    await context.bot.send_message(
        chat_id=user_id,
        text=f"Congratulations! Your registration has been approved.\n\nYour unique ticket code is: `{ticket_code}`",
        parse_mode="Markdown",
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
        text="Unfortunately, your registration could not be approved.",
    )


# --- Event Management ---
@admin_only
async def manage_events(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message or update.callback_query.message
    if update.callback_query:
        await update.callback_query.answer()
    events = db.get_all_events()
    keyboard = []
    if events:
        for event in events:
            prefix = "✅ " if event["is_active"] else ""
            button_text = f"{prefix}{event['name']} ({event['date']})"
            keyboard.append(
                [
                    InlineKeyboardButton(
                        button_text, callback_data=f"view_event_{event['event_id']}"
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
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "Event Management:", reply_markup=reply_markup
        )
    else:
        await message.reply_text("Event Management:", reply_markup=reply_markup)
    return MANAGING_EVENTS


@admin_only
async def view_event_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    event_id = int(query.data.split("_")[2])
    context.user_data["selected_event_id"] = event_id
    event = db.get_event_by_id(event_id)
    if not event:
        await query.edit_message_text("Error: Event not found.")
        return MANAGING_EVENTS
    status = "Active" if event["is_active"] else "Inactive"
    paid_status = f"Paid (${event['fee']:.2f})" if event["is_paid"] else "Free"
    details_text = (
        f"Event: {event['name']}\n"
        f"Description: {event['description']}\n"
        f"Date: {event['date']}\n"
        f"Type: {paid_status}\n"
        f"Reminders: {event['reminders']} hours before\n"
        f"Status: {status}"
    )
    keyboard = [
        [
            InlineKeyboardButton(
                "👥 View Participants", callback_data=f"view_participants_{event_id}"
            )
        ],
    ]
    if event["is_paid"]:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "💰 Manage Discounts", callback_data=f"manage_discounts_{event_id}"
                )
            ]
        )
    if not event["is_active"]:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "🚀 Set Active", callback_data=f"set_active_{event_id}"
                )
            ]
        )
    keyboard.append(
        [
            InlineKeyboardButton(
                "🗑️ Delete Event", callback_data=f"delete_event_{event_id}"
            )
        ]
    )
    keyboard.append(
        [InlineKeyboardButton("⬅️ Back to Event List", callback_data="manage_events")]
    )
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(details_text, reply_markup=reply_markup)
    return VIEWING_EVENT


@admin_only
async def set_active_event_action(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    event_id = int(query.data.split("_")[2])
    db.set_active_event(event_id)
    await query.answer("✅ Event has been set as active.", show_alert=True)
    return await manage_events(update, context)


@admin_only
async def delete_event_action(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    event_id = int(query.data.split("_")[2])
    db.delete_event_by_id(event_id)
    await query.answer("🗑️ Event has been deleted.", show_alert=True)
    return await manage_events(update, context)


# --- Event Creation Flow ---
@admin_only
async def prompt_for_event_name(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Please enter the name for the new event:")
    return GETTING_EVENT_NAME


@admin_only
async def get_event_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["event_name"] = update.message.text
    await update.message.reply_text("Please enter a short description for the event:")
    return GETTING_EVENT_DESC


@admin_only
async def get_event_description(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data["event_description"] = update.message.text
    await update.message.reply_text("Enter the event date in YYYY-MM-DD HH:MM format:")
    return GETTING_EVENT_DATE


@admin_only
async def get_event_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["event_date"] = update.message.text
    keyboard = [
        [
            InlineKeyboardButton("Paid", callback_data="paid"),
            InlineKeyboardButton("Free", callback_data="free"),
        ]
    ]
    await update.message.reply_text(
        "Is this a paid or free event?", reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return GETTING_EVENT_IS_PAID


@admin_only
async def get_event_is_paid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["is_paid"] = query.data == "paid"
    if context.user_data["is_paid"]:
        await query.edit_message_text("Please enter the event fee (e.g., 10.50):")
        return GETTING_EVENT_FEE
    else:
        context.user_data["fee"] = 0.0
        context.user_data["payment_details"] = None
        await query.edit_message_text("Enter reminder hours (e.g., 24, 1):")
        return GETTING_REMINDERS


@admin_only
async def get_event_fee(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["fee"] = float(update.message.text)
    await update.message.reply_text("Please enter payment details (e.g., bank info):")
    return GETTING_PAYMENT_DETAILS


@admin_only
async def get_payment_details(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data["payment_details"] = update.message.text
    await update.message.reply_text("Enter reminder hours (e.g., 24, 1):")
    return GETTING_REMINDERS


@admin_only
async def save_event_and_finish(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data["reminders"] = update.message.text
    try:
        db.create_event(
            name=context.user_data["event_name"],
            description=context.user_data["event_description"],
            date=context.user_data["event_date"],
            fee=context.user_data["fee"],
            is_paid=context.user_data["is_paid"],
            payment_details=context.user_data.get("payment_details"),
            reminders=context.user_data["reminders"],
        )
        await update.message.reply_text(
            f"✅ Event '{context.user_data['event_name']}' created."
        )
    except Exception as e:
        logger.error(f"Failed to save event: {e}", exc_info=True)
        await update.message.reply_text("An error occurred.")
    finally:
        context.user_data.clear()
    return await manage_events(update, context)


# --- Participant Viewer ---
@admin_only
async def view_participants(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    event_id = int(query.data.split("_")[2])
    participants = db.get_participants_for_event(event_id)
    event = db.get_event_by_id(event_id)

    if not participants:
        text = f"No confirmed participants for '{event['name']}' yet."
    else:
        text = f"👥 *Participants for {event['name']} ({len(participants)})*\n\n"
        for p in participants:
            discount_info = (
                f" (Code: {p['discount_code_used']})" if p["discount_code_used"] else ""
            )
            text += f"- @{p['username']}{discount_info}\n"

    keyboard = [
        [
            InlineKeyboardButton(
                "⬅️ Back to Event Details", callback_data=f"view_event_{event_id}"
            )
        ]
    ]
    await query.edit_message_text(
        text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
    )
    return VIEWING_EVENT


# --- Discount Code Management ---
@admin_only
async def manage_discounts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    event_id = int(query.data.split("_")[2])
    context.user_data["selected_event_id"] = event_id

    codes = db.get_discount_codes_for_event(event_id)
    keyboard = []
    text = f"💰 Discount Codes for '{db.get_event_by_id(event_id)['name']}'\n\n"

    if not codes:
        text += "No discount codes created yet."
    else:
        for code in codes:
            value = (
                f"{code['value']}%"
                if code["discount_type"] == "percentage"
                else f"${code['value']:.2f}"
            )
            button_text = f"'{code['code']}' ({value}) - {code['uses_left']} uses left"
            keyboard.append(
                [
                    InlineKeyboardButton(
                        button_text, callback_data=f"view_discount_{code['code_id']}"
                    )
                ]
            )

    keyboard.append(
        [
            InlineKeyboardButton(
                "➕ Create New Code", callback_data=f"create_discount_{event_id}"
            )
        ]
    )
    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅️ Back to Event Details", callback_data=f"view_event_{event_id}"
            )
        ]
    )

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return MANAGING_DISCOUNTS


@admin_only
async def view_discount_details(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Shows details for a specific discount code and offers a delete option."""
    query = update.callback_query
    await query.answer()
    code_id = int(query.data.split("_")[2])
    event_id = context.user_data["selected_event_id"]

    keyboard = [
        [
            InlineKeyboardButton(
                "🗑️ Delete this Code", callback_data=f"delete_code_{code_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Back to Discount List", callback_data=f"manage_discounts_{event_id}"
            )
        ],
    ]
    await query.edit_message_text(
        "Are you sure you want to delete this discount code?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return DELETING_DISCOUNT


@admin_only
async def delete_discount_action(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Deletes a discount code."""
    query = update.callback_query
    await query.answer()
    code_id = int(query.data.split("_")[2])
    event_id = context.user_data["selected_event_id"]

    db.delete_discount_code(code_id)
    await query.answer("Discount code deleted.", show_alert=True)

    # Re-call manage_discounts to show the updated list
    query.data = f"manage_discounts_{event_id}"  # Trick the handler
    return await manage_discounts(update, context)


@admin_only
async def prompt_for_discount_code(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Please enter the discount code text (e.g., SUMMER25):"
    )
    return GETTING_DISCOUNT_CODE


@admin_only
async def get_discount_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["discount_code"] = update.message.text.upper()
    keyboard = [
        [
            InlineKeyboardButton("Percentage %", callback_data="percentage"),
            InlineKeyboardButton("Fixed Amount $", callback_data="fixed"),
        ]
    ]
    await update.message.reply_text(
        "What type of discount is this?", reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return GETTING_DISCOUNT_TYPE


@admin_only
async def get_discount_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["discount_type"] = query.data
    prompt = (
        "Enter the percentage value (e.g., 20 for 20%):"
        if query.data == "percentage"
        else "Enter the fixed amount (e.g., 5.50 for $5.50):"
    )
    await query.edit_message_text(prompt)
    return GETTING_DISCOUNT_VALUE


@admin_only
async def get_discount_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["discount_value"] = float(update.message.text)
    await update.message.reply_text("How many times can this code be used?")
    return GETTING_DISCOUNT_USES


@admin_only
async def save_discount_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["discount_uses"] = int(update.message.text)
    event_id = context.user_data["selected_event_id"]
    try:
        db.create_discount_code(
            event_id=event_id,
            code=context.user_data["discount_code"],
            discount_type=context.user_data["discount_type"],
            value=context.user_data["discount_value"],
            uses_left=context.user_data["discount_uses"],
        )
        await update.message.reply_text(
            f"✅ Discount code '{context.user_data['discount_code']}' created."
        )
    except Exception as e:
        logger.error(f"Failed to save discount code: {e}", exc_info=True)
        await update.message.reply_text(
            "An error occurred. This code might already exist for this event."
        )

    # To go back to the discount list, we need to call manage_discounts.
    # We'll simulate a callback query for this.
    class FakeQuery:
        def __init__(self, msg, data):
            self.message = msg
            self.data = data

        async def answer(self):
            pass

    fake_update = Update(
        update.update_id,
        callback_query=FakeQuery(update.message, f"manage_discounts_{event_id}"),
    )
    context.user_data.clear()
    return await manage_discounts(fake_update, context)


# --- General ---
@admin_only
async def cancel_admin_conversation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text("Admin action cancelled.")
    else:
        await update.message.reply_text("Admin action cancelled.")
    context.user_data.clear()
    return ConversationHandler.END
