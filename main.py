import logging
import subprocess
import time
import signal
import os
import sys
from logging_config import setup_loggers
from config import (
    BOT_RESTART_DELAY,
    HEARTBEAT_FILE,
    HEARTBEAT_INTERVAL,
    HEARTBEAT_TIMEOUT,
)

# --- Setup ---
setup_loggers()
log = logging.getLogger()
bot_process = None

# --- CRITICAL: Build absolute paths ---
# This ensures the script can find the venv and bot_process.py
# regardless of where it's run from (e.g., systemd).
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_EXECUTABLE = os.path.join(SCRIPT_DIR, "venv", "bin", "python")
BOT_SCRIPT_PATH = os.path.join(SCRIPT_DIR, "bot_process.py")


def start_bot_process():
    """Launches the bot as a separate process using the correct virtual environment."""
    global bot_process
    log.info(f"Launching bot process: {PYTHON_EXECUTABLE} {BOT_SCRIPT_PATH}")
    try:
        # We use the absolute path to the Python interpreter in the venv
        # and the absolute path to the bot script.
        bot_process = subprocess.Popen([PYTHON_EXECUTABLE, BOT_SCRIPT_PATH])
        if os.path.exists(HEARTBEAT_FILE):
            os.remove(HEARTBEAT_FILE)
    except FileNotFoundError:
        log.critical(
            f"Could not find Python executable at '{PYTHON_EXECUTABLE}'. "
            "Please ensure the virtual environment path in main.py is correct."
        )
        sys.exit(1)
    except Exception as e:
        log.critical(f"Failed to start bot process: {e}", exc_info=True)
        sys.exit(1)


def handle_shutdown_signal(signum, frame):
    """Gracefully shuts down the watchdog and the bot process."""
    log.info("Watchdog received shutdown signal (Ctrl+C). Terminating.")
    if bot_process and bot_process.poll() is None:
        log.info("Terminating bot process...")
        bot_process.terminate()
        bot_process.wait()
    log.info("Isocrates Bot watchdog has been shut down.")
    sys.exit(0)


signal.signal(signal.SIGINT, handle_shutdown_signal)
signal.signal(signal.SIGTERM, handle_shutdown_signal)


if __name__ == "__main__":
    log.info("Starting Isocrates Bot watchdog...")
    start_bot_process()

    while True:
        try:
            time.sleep(HEARTBEAT_INTERVAL * 2)

            bot_is_running = bot_process.poll() is None
            heartbeat_is_stale = False
            heartbeat_file_missing = not os.path.exists(HEARTBEAT_FILE)

            if not heartbeat_file_missing:
                last_heartbeat = os.path.getmtime(HEARTBEAT_FILE)
                if (time.time() - last_heartbeat) > HEARTBEAT_TIMEOUT:
                    heartbeat_is_stale = True

            # If the bot is running but the heartbeat is bad, it's frozen.
            if bot_is_running and (heartbeat_is_stale or heartbeat_file_missing):
                log.error(
                    "Heartbeat is stale or missing. The bot process appears to be frozen. Terminating and restarting..."
                )
                bot_process.terminate()
                bot_process.wait()
                start_bot_process()

            # If the bot process has stopped for any reason, restart it.
            elif not bot_is_running:
                log.error(
                    f"Bot process stopped unexpectedly (exit code: {bot_process.returncode}). Restarting..."
                )
                start_bot_process()

        except KeyboardInterrupt:
            # This is handled by the signal handler, but we keep it here as a fallback.
            break
        except Exception as e:
            log.critical(f"Watchdog encountered a critical error: {e}", exc_info=True)
            # Wait before retrying to prevent rapid-fire crash loops
            time.sleep(BOT_RESTART_DELAY)
