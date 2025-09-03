import logging
from telegram.ext import (
    Application,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    JobQueue,
)
from config import *
from . import handlers, admin, scheduler

logger = logging.getLogger()


async def error_handler(update, context):
    logger.error("Exception while handling an update:", exc_info=context.error)


def run_bot() -> None:
    job_queue = JobQueue()
    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .connect_timeout(CONNECT_TIMEOUT)
        .read_timeout(READ_TIMEOUT)
        .job_queue(job_queue)
        .build()
    )

    application.add_error_handler(error_handler)
    application.job_queue.run_repeating(
        scheduler.check_and_send_reminders, interval=60, first=10
    )

    user_entry_points = [CommandHandler("start", handlers.start)]
    admin_entry_points = [CommandHandler("admin", admin.admin_panel)]

    admin_conv_handler = ConversationHandler(
        entry_points=admin_entry_points,
        states={
            ADMIN_CHOOSING: [
                CallbackQueryHandler(
                    admin.view_pending_registrations, pattern="^view_pending$"
                ),
                CallbackQueryHandler(admin.manage_events, pattern="^manage_events$"),
            ],
            MANAGING_EVENTS: [
                CallbackQueryHandler(admin.view_event_details, pattern="^view_event_"),
                CallbackQueryHandler(
                    admin.prompt_for_event_name, pattern="^create_event$"
                ),
                CallbackQueryHandler(admin.admin_panel, pattern="^admin_back$"),
            ],
            VIEWING_EVENT: [
                CallbackQueryHandler(
                    admin.set_active_event_action, pattern="^set_active_"
                ),
                CallbackQueryHandler(
                    admin.delete_event_action, pattern="^delete_event_"
                ),
                CallbackQueryHandler(
                    admin.manage_discounts, pattern="^manage_discounts_"
                ),
                CallbackQueryHandler(
                    admin.view_participants, pattern="^view_participants_"
                ),
                CallbackQueryHandler(admin.manage_events, pattern="^manage_events$"),
                # --- BUG FIX: Added handler for the "Back to Event Details" button ---
                CallbackQueryHandler(admin.view_event_details, pattern="^view_event_"),
            ],
            GETTING_EVENT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin.get_event_name)
            ],
            GETTING_EVENT_DESC: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, admin.get_event_description
                )
            ],
            GETTING_EVENT_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin.get_event_date)
            ],
            GETTING_EVENT_FEE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin.get_event_fee)
            ],
            GETTING_EVENT_IS_PAID: [
                CallbackQueryHandler(admin.get_event_is_paid, pattern="^(paid|free)$")
            ],
            GETTING_PAYMENT_DETAILS: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, admin.get_payment_details
                )
            ],
            GETTING_REMINDERS: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, admin.save_event_and_finish
                )
            ],
            MANAGING_DISCOUNTS: [
                CallbackQueryHandler(
                    admin.prompt_for_discount_code, pattern="^create_discount_"
                ),
                CallbackQueryHandler(admin.view_event_details, pattern="^view_event_"),
            ],
            GETTING_DISCOUNT_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin.get_discount_code)
            ],
            GETTING_DISCOUNT_TYPE: [
                CallbackQueryHandler(
                    admin.get_discount_type, pattern="^(percentage|fixed)$"
                )
            ],
            GETTING_DISCOUNT_VALUE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, admin.get_discount_value
                )
            ],
            GETTING_DISCOUNT_USES: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, admin.save_discount_code
                )
            ],
        },
        fallbacks=[CommandHandler("cancel", admin.cancel_admin_conversation)]
        + admin_entry_points,
        per_message=False,
    )

    user_conv_handler = ConversationHandler(
        entry_points=user_entry_points,
        states={
            CHOOSING: [
                MessageHandler(
                    filters.Regex("^(Yes, Register Me!|No, thanks.)$"),
                    handlers.handle_choice,
                )
            ],
            AWAITING_DISCOUNT_PROMPT: [
                MessageHandler(
                    filters.Regex("^(Yes|No)$"), handlers.handle_discount_prompt
                )
            ],
            AWAITING_DISCOUNT_CODE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, handlers.handle_discount_code
                )
            ],
            AWAITING_RECEIPT: [MessageHandler(filters.PHOTO, handlers.handle_receipt)],
        },
        fallbacks=[CommandHandler("cancel", handlers.cancel)] + user_entry_points,
        per_message=False,
    )

    application.add_handler(user_conv_handler)
    application.add_handler(admin_conv_handler)
    application.add_handler(CommandHandler("myreferral", handlers.my_referral))
    application.add_handler(CommandHandler("help", handlers.help_command))
    application.add_handler(
        CallbackQueryHandler(admin.handle_registration_approval, pattern="^approve_")
    )
    application.add_handler(
        CallbackQueryHandler(admin.handle_registration_rejection, pattern="^reject_")
    )

    logger.info("Bot is running...")
    application.run_polling()
