import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)
import database as db
from .utils import admin_only, format_toman, get_user_info
from config import *

interactions_logger = logging.getLogger("interactions")
app_logger = logging.getLogger("app")


@admin_only
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Resets any ongoing admin conversation and displays the main admin panel."""
    user = update.effective_user
    # Clear any leftover data from previous admin conversations to ensure a clean start.
    context.user_data.clear()
    interactions_logger.info(
        f"ADMIN {get_user_info(user)} opened the admin panel (state reset)."
    )

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
    text = "Admin Control Panel:"
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await message.reply_text(text, reply_markup=reply_markup)
    return ADMIN_CHOOSING


@admin_only
async def view_pending_registrations(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    user = update.effective_user
    interactions_logger.info(
        f"ADMIN {get_user_info(user)} chose to view pending registrations."
    )
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
        f"Fee Paid: {format_toman(final_fee)}\n"
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
    query = update.callback_query
    user = update.effective_user
    _, reg_id, target_user_id = query.data.split("_")
    interactions_logger.info(
        f"ADMIN {get_user_info(user)} approved registration [ID:{reg_id}] for User [ID:{target_user_id}]."
    )
    await query.answer()

    ticket_code = db.update_registration_status(int(reg_id), "confirmed")
    await query.edit_message_caption(caption=f"✅ Registration {reg_id} approved.")
    await context.bot.send_message(
        chat_id=target_user_id,
        text=f"Congratulations! Your registration has been approved.\n\nYour unique ticket code is: {ticket_code}",
    )


@admin_only
async def handle_registration_rejection(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    user = update.effective_user
    _, reg_id, target_user_id = query.data.split("_")
    interactions_logger.info(
        f"ADMIN {get_user_info(user)} rejected registration [ID:{reg_id}] for User [ID:{target_user_id}]."
    )
    await query.answer()

    db.update_registration_status(int(reg_id), "rejected")
    await query.edit_message_caption(caption=f"❌ Registration {reg_id} rejected.")
    await context.bot.send_message(
        chat_id=target_user_id,
        text="Unfortunately, your registration could not be approved.",
    )


@admin_only
async def manage_events(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    interactions_logger.info(f"ADMIN {get_user_info(user)} entered event management.")

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

    text = "Event Management:"
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await message.reply_text(text, reply_markup=reply_markup)
    return MANAGING_EVENTS


@admin_only
async def view_event_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user = update.effective_user
    await query.answer()

    event_id = int(query.data.split("_")[2])
    interactions_logger.info(
        f"ADMIN {get_user_info(user)} is viewing details for Event [ID:{event_id}]."
    )
    context.user_data["selected_event_id"] = event_id

    event = db.get_event_by_id(event_id)
    if not event:
        await query.edit_message_text("Error: Event not found.")
        return MANAGING_EVENTS

    status = "Active" if event["is_active"] else "Inactive"
    paid_status = f"Paid ({format_toman(event['fee'])})" if event["is_paid"] else "Free"
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
        ]
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
    user = update.effective_user
    await query.answer()

    event_id = int(query.data.split("_")[2])
    interactions_logger.info(
        f"ADMIN {get_user_info(user)} set Event [ID:{event_id}] as active."
    )
    db.set_active_event(event_id)

    await query.answer("✅ Event has been set as active.", show_alert=True)
    return await manage_events(update, context)


@admin_only
async def delete_event_action(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    user = update.effective_user
    await query.answer()

    event_id = int(query.data.split("_")[2])
    interactions_logger.warning(
        f"ADMIN {get_user_info(user)} DELETED Event [ID:{event_id}]."
    )
    db.delete_event_by_id(event_id)

    await query.answer("🗑️ Event has been deleted.", show_alert=True)
    return await manage_events(update, context)


@admin_only
async def prompt_for_event_name(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    user = update.effective_user
    interactions_logger.info(
        f"ADMIN {get_user_info(user)} started creating a new event."
    )
    await query.answer()
    await query.edit_message_text("Please enter the name for the new event:")
    return GETTING_EVENT_NAME


@admin_only
async def get_event_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    context.user_data["event_name"] = update.message.text
    interactions_logger.info(
        f"ADMIN {get_user_info(user)} (Event Creation) set name: '{update.message.text}'."
    )
    await update.message.reply_text("Please enter a short description for the event:")
    return GETTING_EVENT_DESC


@admin_only
async def get_event_description(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    user = update.effective_user
    context.user_data["event_description"] = update.message.text
    interactions_logger.info(
        f"ADMIN {get_user_info(user)} (Event Creation) set description: '{update.message.text}'."
    )
    await update.message.reply_text("Enter the event date in YYYY-MM-DD HH:MM format:")
    return GETTING_EVENT_DATE


@admin_only
async def get_event_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    context.user_data["event_date"] = update.message.text
    interactions_logger.info(
        f"ADMIN {get_user_info(user)} (Event Creation) set date: '{update.message.text}'."
    )
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
    user = update.effective_user
    await query.answer()

    context.user_data["is_paid"] = query.data == "paid"
    interactions_logger.info(
        f"ADMIN {get_user_info(user)} (Event Creation) set is_paid: {context.user_data['is_paid']}."
    )

    if context.user_data["is_paid"]:
        await query.edit_message_text(
            "Please enter the event fee in Toman (e.g., 150000):"
        )
        return GETTING_EVENT_FEE
    else:
        context.user_data["fee"] = 0.0
        context.user_data["payment_details"] = None
        await query.edit_message_text("Enter reminder hours (e.g., 24, 1):")
        return GETTING_REMINDERS


@admin_only
async def get_event_fee(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    context.user_data["fee"] = float(update.message.text)
    interactions_logger.info(
        f"ADMIN {get_user_info(user)} (Event Creation) set fee: {update.message.text}."
    )
    await update.message.reply_text(
        "Please enter the full payment instructions. You can use the placeholder '{final_fee}' to show the calculated price.\n\n"
        "Example:\nPlease pay {final_fee} to account 12345."
    )
    return GETTING_PAYMENT_DETAILS


@admin_only
async def get_payment_details(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    user = update.effective_user
    context.user_data["payment_details"] = update.message.text
    interactions_logger.info(
        f"ADMIN {get_user_info(user)} (Event Creation) set payment details: '{update.message.text}'."
    )
    await update.message.reply_text("Enter reminder hours (e.g., 24, 1):")
    return GETTING_REMINDERS


@admin_only
async def save_event_and_finish(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    user = update.effective_user
    context.user_data["reminders"] = update.message.text
    interactions_logger.info(
        f"ADMIN {get_user_info(user)} (Event Creation) set reminders: '{update.message.text}'. Saving event."
    )

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
        app_logger.info(
            f"Event '{context.user_data['event_name']}' created by ADMIN {get_user_info(user)}."
        )
    except Exception as e:
        app_logger.error(f"Failed to save event: {e}", exc_info=True)
        await update.message.reply_text("An error occurred while saving the event.")
    finally:
        context.user_data.clear()

    return await manage_events(update, context)


@admin_only
async def view_participants(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user = update.effective_user
    await query.answer()
    event_id = int(query.data.split("_")[2])
    interactions_logger.info(
        f"ADMIN {get_user_info(user)} viewed participants for Event [ID:{event_id}]."
    )
    participants = db.get_participants_for_event(event_id)
    event = db.get_event_by_id(event_id)

    event_name = event["name"]

    if not participants:
        text = f"No confirmed participants for '{event_name}' yet."
    else:
        text = f"Participants for {event_name} ({len(participants)}):\n\n"
        for p in participants:
            discount_info = ""
            if p["discount_code_used"]:
                discount_info = f" (Code: {p['discount_code_used']})"
            text += f"- @{p['username']}{discount_info}\n"

    keyboard = [
        [
            InlineKeyboardButton(
                "⬅️ Back to Event Details", callback_data=f"view_event_{event_id}"
            )
        ]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return VIEWING_EVENT


# --- Discount Code Management ---
@admin_only
async def manage_discounts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # This function now handles both callback queries and message-driven transitions
    query = update.callback_query
    message = update.message
    user = update.effective_user

    if query:
        await query.answer()
        event_id = int(query.data.split("_")[2])
        interactions_logger.info(
            f"ADMIN {get_user_info(user)} entered discount management for Event [ID:{event_id}] via callback."
        )
    else:  # This case is for after creating a code
        event_id = context.user_data["selected_event_id"]
        interactions_logger.info(
            f"ADMIN {get_user_info(user)} returned to discount management for Event [ID:{event_id}] after action."
        )

    context.user_data["selected_event_id"] = event_id
    codes = db.get_discount_codes_for_event(event_id)
    event = db.get_event_by_id(event_id)
    text = f"Discount Codes for '{event['name']}'\n\n"

    keyboard = []
    if not codes:
        text += "No discount codes created yet."
    else:
        for code in codes:
            value = (
                f"{int(code['value'])}%"
                if code["discount_type"] == "percentage"
                else f"{format_toman(code['value'])}"
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
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(text, reply_markup=reply_markup)
    elif message:
        await message.reply_text(text, reply_markup=reply_markup)

    return MANAGING_DISCOUNTS


@admin_only
async def view_discount_details(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
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
                "⬅️ Back to Discount List",
                callback_data=f"manage_discounts_{event_id}",
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
    query = update.callback_query
    user = update.effective_user
    await query.answer()
    code_id = int(query.data.split("_")[2])
    event_id = context.user_data["selected_event_id"]
    interactions_logger.warning(
        f"ADMIN {get_user_info(user)} deleted Discount [ID:{code_id}] from Event [ID:{event_id}]."
    )
    db.delete_discount_code(code_id)
    await query.answer("Discount code deleted.", show_alert=True)

    # We need to pass a proper update object back to manage_discounts
    query.data = f"manage_discounts_{event_id}"
    return await manage_discounts(update, context)


@admin_only
async def prompt_for_discount_code(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    user = update.effective_user
    interactions_logger.info(
        f"ADMIN {get_user_info(user)} started creating a new discount code."
    )
    await query.answer()
    await query.edit_message_text(
        "Please enter the discount code text (e.g., SUMMER25):"
    )
    return GETTING_DISCOUNT_CODE


@admin_only
async def get_discount_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    context.user_data["discount_code"] = update.message.text.upper()
    interactions_logger.info(
        f"ADMIN {get_user_info(user)} (Discount Creation) set code: '{context.user_data['discount_code']}'."
    )
    keyboard = [
        [
            InlineKeyboardButton("Percentage %", callback_data="percentage"),
            InlineKeyboardButton("Fixed Amount (Toman)", callback_data="fixed"),
        ]
    ]
    await update.message.reply_text(
        "What type of discount is this?", reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return GETTING_DISCOUNT_TYPE


@admin_only
async def get_discount_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user = update.effective_user
    await query.answer()
    context.user_data["discount_type"] = query.data
    interactions_logger.info(
        f"ADMIN {get_user_info(user)} (Discount Creation) set type: '{context.user_data['discount_type']}'."
    )
    prompt = (
        "Enter the percentage value (e.g., 20 for 20%):"
        if query.data == "percentage"
        else "Enter the fixed amount in Toman (e.g., 50000):"
    )
    await query.edit_message_text(prompt)
    return GETTING_DISCOUNT_VALUE


@admin_only
async def get_discount_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    context.user_data["discount_value"] = float(update.message.text)
    interactions_logger.info(
        f"ADMIN {get_user_info(user)} (Discount Creation) set value: {context.user_data['discount_value']}."
    )
    await update.message.reply_text("How many times can this code be used?")
    return GETTING_DISCOUNT_USES


@admin_only
async def save_discount_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    context.user_data["discount_uses"] = int(update.message.text)
    event_id = context.user_data["selected_event_id"]
    interactions_logger.info(
        f"ADMIN {get_user_info(user)} (Discount Creation) set uses: {context.user_data['discount_uses']}. Saving."
    )
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
        app_logger.error(f"Failed to save discount code: {e}", exc_info=True)
        await update.message.reply_text(
            "An error occurred. This code might already exist for this event."
        )

    # After saving, we transition back to the manage_discounts state.
    # We pass the original update object, which contains the message.
    # The manage_discounts function will handle it correctly.
    return await manage_discounts(update, context)


@admin_only
async def cancel_admin_conversation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    user = update.effective_user
    interactions_logger.info(
        f"ADMIN {get_user_info(user)} cancelled the admin conversation."
    )

    text = "Admin action cancelled."
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(text)
    else:
        await update.message.reply_text(text)

    context.user_data.clear()
    return ConversationHandler.END
