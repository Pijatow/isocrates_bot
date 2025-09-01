from telegram.ext import (
    Application,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
from config import TELEGRAM_BOT_TOKEN, CHOOSING
from . import handlers


def run_bot() -> None:
    """
    Sets up the application and runs the bot.
    """
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

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

    print("Bot is running...")
    # Run the bot until the user presses Ctrl-C
    application.run_polling()
