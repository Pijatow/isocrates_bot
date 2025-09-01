import logging
from telegram.ext import (
    Application,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
from config import (
    TELEGRAM_BOT_TOKEN,
    CHOOSING,
    AWAITING_RECEIPT,
    CONNECT_TIMEOUT,
    READ_TIMEOUT,
)
from . import handlers

# Get the root logger
logger = logging.getLogger()


async def error_handler(update, context):
    """
    Global error handler. Logs all uncaught exceptions.
    """
    logger.error("Exception while handling an update:", exc_info=context.error)


def run_bot() -> None:
    """
    Sets up the application and runs the bot.
    """
    application_builder = Application.builder().token(TELEGRAM_BOT_TOKEN)
    application_builder.connect_timeout(CONNECT_TIMEOUT)
    application_builder.read_timeout(READ_TIMEOUT)
    application = application_builder.build()

    application.add_error_handler(error_handler)

    # --- Conversation Handler Setup ---
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", handlers.start)],
        states={
            CHOOSING: [
                MessageHandler(
                    filters.Regex("^(Yes, Register Me!|No, thanks.)$"),
                    handlers.handle_choice,
                )
            ],
            AWAITING_RECEIPT: [MessageHandler(filters.PHOTO, handlers.handle_receipt)],
        },
        fallbacks=[CommandHandler("cancel", handlers.cancel)],
    )

    application.add_handler(conv_handler)

    logger.info("Bot is running...")
    application.run_polling()
