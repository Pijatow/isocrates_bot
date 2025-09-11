import subprocess
import time
import logging
import os
from logging_config import setup_loggers
from config import BOT_RESTART_DELAY, HEARTBEAT_TIMEOUT

# Define the path for the heartbeat file
HEARTBEAT_FILE = os.path.join("logs", "heartbeat.log")

if __name__ == "__main__":
    """
    This script is the main watchdog for the Isocrates Bot.
    It runs the bot in a separate process and monitors a "heartbeat" file.
    If the heartbeat stops updating or the file is missing, the watchdog assumes
    the bot is frozen or has self-terminated, kills the process, and launches a new one.
    """
    setup_loggers()
    logging.info("--- Starting Isocrates Bot Watchdog ---")

    bot_process = None
    while True:
        try:
            logging.info("Launching bot process...")
            bot_process = subprocess.Popen(["python3", "bot_process.py"])

            # Give the bot a moment to start up and create the first heartbeat
            time.sleep(10)

            # --- Monitoring Loop ---
            while bot_process.poll() is None:  # While the bot process is running
                heartbeat_ok = False
                if os.path.exists(HEARTBEAT_FILE):
                    try:
                        with open(HEARTBEAT_FILE, "r") as f:
                            last_heartbeat = float(f.read())

                        if time.time() - last_heartbeat < HEARTBEAT_TIMEOUT:
                            heartbeat_ok = True
                        else:
                            logging.warning(
                                f"Bot heartbeat is stale (last seen {int(time.time() - last_heartbeat)}s ago). Process appears frozen."
                            )
                    except (ValueError, IOError) as e:
                        logging.warning(f"Could not read heartbeat file: {e}")
                else:
                    logging.warning(
                        "Heartbeat file not found. Assuming bot has self-terminated or failed to start."
                    )

                if not heartbeat_ok:
                    logging.error("Terminating unresponsive bot process...")
                    bot_process.terminate()
                    time.sleep(5)  # Give it time to die
                    break  # Exit monitoring loop to trigger restart

                # Check the heartbeat file periodically
                time.sleep(20)

            # --- Restart Logic ---
            # This code is reached if the process terminates on its own OR if we terminated it.
            exit_code = bot_process.returncode
            logging.error(
                f"Bot process has terminated with exit code {exit_code}. Restarting in {BOT_RESTART_DELAY} seconds..."
            )
            time.sleep(BOT_RESTART_DELAY)

        except KeyboardInterrupt:
            logging.info(
                "Watchdog received shutdown signal (Ctrl+C). Terminating bot process."
            )
            if bot_process and bot_process.poll() is None:
                bot_process.terminate()
            break
        except Exception as e:
            logging.critical(
                f"Watchdog encountered a critical error: {e}", exc_info=True
            )
            if bot_process and bot_process.poll() is None:
                bot_process.terminate()
            time.sleep(BOT_RESTART_DELAY)

    logging.info("--- Isocrates Bot Watchdog has shut down. ---")
