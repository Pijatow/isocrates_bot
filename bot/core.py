import logging
from telegram.ext import (
    Application,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
from config import TELEGRAM_BOT_TOKEN, CHOOSING, CONNECT_TIMEOUT, READ_TIMEOUT
from . import handlers

# Get the root logger
logger = logging.getLogger()


async def error_handler(update, context):
    """
    Global error handler. Logs all uncaught exceptions.
    This is a safety net to prevent the bot from crashing.
    """
    logger.error("Exception while handling an update:", exc_info=context.error)
    # Optionally, you can add logic here to notify an admin about the error.


def run_bot() -> None:
    """
    Sets up the application and runs the bot.
    """
    # Create the Application builder and configure it.
    application_builder = Application.builder().token(TELEGRAM_BOT_TOKEN)

    # Set global timeouts for all network requests
    application_builder.connect_timeout(CONNECT_TIMEOUT)
    application_builder.read_timeout(READ_TIMEOUT)

    # Build the application
    application = application_builder.build()

    # --- Register the global error handler ---
    application.add_error_handler(error_handler)

    # --- Conversation Handler Setup ---
    # This handler manages the registration flow.
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", handlers.start)],
        states={
            CHOOSING: [
                MessageHandler(
                    filters.Regex("^(Yes, Register Me!|No, thanks.)$"),
                    handlers.handle_choice,
                )
            ],
            # Future states like 'AWAITING_RECEIPT' will be added here.
        },
        fallbacks=[CommandHandler("cancel", handlers.cancel)],
    )

    # Add the conversation handler to the application
    application.add_handler(conv_handler)

    logger.info("Bot is running...")
    # Run the bot until the user presses Ctrl-C
    application.run_polling()
