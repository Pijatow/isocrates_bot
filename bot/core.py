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
from config import (
    TELEGRAM_BOT_TOKEN,
    CHOOSING,
    AWAITING_RECEIPT,
    CONNECT_TIMEOUT,
    READ_TIMEOUT,
    ADMIN_CHOOSING,
    MANAGING_EVENTS,
    VIEWING_EVENT,
    GETTING_EVENT_NAME,
    GETTING_EVENT_DESC,
    GETTING_EVENT_DATE,
    GETTING_EVENT_IS_PAID,
    GETTING_PAYMENT_DETAILS,
    GETTING_REMINDERS,
)
from . import handlers
from . import admin
from . import scheduler

logger = logging.getLogger()


async def error_handler(update, context):
    """Global error handler."""
    logger.error("Exception while handling an update:", exc_info=context.error)


def run_bot() -> None:
    """Sets up the application, schedules jobs, and runs the bot."""
    job_queue = JobQueue()

    application_builder = Application.builder().token(TELEGRAM_BOT_TOKEN)
    application_builder.connect_timeout(CONNECT_TIMEOUT)
    application_builder.read_timeout(READ_TIMEOUT)
    application_builder.job_queue(job_queue)
    application = application_builder.build()

    application.add_error_handler(error_handler)

    application.job_queue.run_repeating(
        scheduler.check_and_send_reminders, interval=60, first=10
    )

    # Define entry points for conversations
    user_entry_points = [CommandHandler("start", handlers.start)]
    admin_entry_points = [CommandHandler("admin", admin.admin_panel)]

    admin_conversation_handler = ConversationHandler(
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
                CallbackQueryHandler(admin.manage_events, pattern="^manage_events$"),
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
            AWAITING_RECEIPT: [MessageHandler(filters.PHOTO, handlers.handle_receipt)],
        },
        fallbacks=[CommandHandler("cancel", handlers.cancel)] + user_entry_points,
        per_message=False,
    )

    application.add_handler(user_conv_handler)
    application.add_handler(admin_conversation_handler)

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
