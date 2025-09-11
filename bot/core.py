import logging
import asyncio
import time
import os
import sys
from telegram.ext import (
    Application,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    JobQueue,
)
from telegram.error import NetworkError
from config import *
from . import handlers, admin, scheduler

app_logger = logging.getLogger("app")
network_logger = logging.getLogger("network")

# Define the path for the heartbeat file within the logs directory
HEARTBEAT_FILE = os.path.join("logs", "heartbeat.log")


async def error_handler(update, context):
    """
    Logs exceptions. If the exception is a critical and unrecoverable
    network error, it initiates a controlled shutdown of the bot process
    so the watchdog can restart it cleanly.
    """
    err_text = str(context.error)
    network_logger.error(
        f"Exception while handling an update: {err_text}", exc_info=context.error
    )

    # --- Controlled Shutdown Trigger ---
    # This specific error indicates the polling loop is likely dead and unrecoverable.
    if "httpx.ConnectError" in err_text:
        network_logger.critical(
            "Unrecoverable ConnectError detected. Initiating self-shutdown."
        )
        try:
            # Delete the heartbeat file to signal the watchdog immediately
            os.remove(HEARTBEAT_FILE)
            network_logger.info("Heartbeat file removed.")
        except OSError as e:
            network_logger.error(f"Could not remove heartbeat file: {e}")

        # Exit the process with an error code. The watchdog will see this and restart.
        sys.exit(1)


async def update_heartbeat():
    """
    Periodically writes a timestamp to a file in the logs directory.
    The watchdog process monitors this file to ensure the bot is still alive.
    """
    while True:
        try:
            with open(HEARTBEAT_FILE, "w") as f:
                f.write(str(time.time()))
        except Exception as e:
            app_logger.error(f"Failed to write heartbeat: {e}")
        await asyncio.sleep(HEARTBEAT_INTERVAL)


async def post_init(application: Application) -> None:
    """
    This function is called after the Application is initialized.
    It's the perfect place to start background tasks.
    """
    asyncio.create_task(update_heartbeat())


def run_bot() -> None:
    """
    Initializes and runs the bot application. The heartbeat task is
    started automatically by the post_init hook.
    """
    job_queue = JobQueue()
    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .connect_timeout(CONNECT_TIMEOUT)
        .read_timeout(READ_TIMEOUT)
        .job_queue(job_queue)
        .post_init(post_init)
        .http_version("1.1")
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
                CallbackQueryHandler(
                    admin.view_discount_details, pattern="^view_discount_"
                ),
                CallbackQueryHandler(admin.view_event_details, pattern="^view_event_"),
            ],
            DELETING_DISCOUNT: [
                CallbackQueryHandler(
                    admin.delete_discount_action, pattern="^delete_code_"
                ),
                CallbackQueryHandler(
                    admin.manage_discounts, pattern="^manage_discounts_"
                ),
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
    application.add_handler(CommandHandler("myticket", handlers.my_ticket))
    application.add_handler(
        CallbackQueryHandler(admin.handle_registration_approval, pattern="^approve_")
    )
    application.add_handler(
        CallbackQueryHandler(admin.handle_registration_rejection, pattern="^reject_")
    )

    app_logger.info("Bot polling started...")
    # --- THIS IS THE KEY CHANGE ---
    # By setting drop_pending_updates to False, the bot will process all messages
    # that were sent while it was offline.
    application.run_polling(drop_pending_updates=False)
