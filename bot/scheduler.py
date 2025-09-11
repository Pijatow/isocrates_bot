import logging
from datetime import datetime, timedelta
import database as db

# Use the dedicated scheduler logger
logger = logging.getLogger("scheduler")


async def check_and_send_reminders(context):
    """
    Checks for upcoming events and sends reminders to confirmed attendees.
    """
    logger.debug("Scheduler running: Checking for reminders to send.")
    try:
        events = db.get_events_with_pending_reminders()
        now = datetime.now()

        for event in events:
            event_id = event["event_id"]
            event_name = event["name"]
            event_date_str = event["date"]
            reminder_hours = [int(h.strip()) for h in event["reminders"].split(",")]

            try:
                event_date = datetime.strptime(event_date_str, "%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                logger.error(
                    f"Invalid date format for event {event_id}: '{event_date_str}'"
                )
                continue

            for hour in reminder_hours:
                reminder_time = event_date - timedelta(hours=hour)
                # Check if the reminder time is within the last minute
                if now >= reminder_time and (now - reminder_time).total_seconds() < 60:
                    attendees = db.get_confirmed_attendees(event_id)
                    if not attendees:
                        logger.info(
                            f"Reminder triggered for '{event_name}', but there are no confirmed attendees."
                        )
                        continue

                    logger.info(
                        f"Sending {hour}-hour reminder for event '{event_name}' to {len(attendees)} attendees."
                    )
                    for user_id in attendees:
                        message = f"📢 Reminder: The event '{event_name}' is starting in approximately {hour} hour(s)!"
                        try:
                            await context.bot.send_message(
                                chat_id=user_id, text=message
                            )
                        except Exception as e:
                            logger.error(
                                f"Failed to send reminder to user {user_id} for event {event_id}: {e}"
                            )

    except Exception as e:
        logger.error(f"Error in scheduler job: {e}", exc_info=True)
