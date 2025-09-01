import sqlite3
import logging
from config import DATABASE_NAME

logger = logging.getLogger()


def init_db():
    """Initializes the database and creates tables if they don't exist."""
    try:
        con = sqlite3.connect(DATABASE_NAME)
        cur = con.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS registrations (
                registration_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL, status TEXT NOT NULL,
                receipt_file_id TEXT, registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            """
        )
        con.commit()
        con.close()
        logger.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        raise


def add_or_update_user(user_id: int, username: str, first_name: str):
    """Adds or updates a user in the database."""
    con = sqlite3.connect(DATABASE_NAME)
    cur = con.cursor()
    cur.execute(
        """
        INSERT INTO users (user_id, username, first_name) VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET username=excluded.username, first_name=excluded.first_name
        """,
        (user_id, username, first_name),
    )
    con.commit()
    con.close()


def create_registration(user_id: int, status: str, receipt_file_id: str = None):
    """Creates a new registration record."""
    con = sqlite3.connect(DATABASE_NAME)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO registrations (user_id, status, receipt_file_id) VALUES (?, ?, ?)",
        (user_id, status, receipt_file_id),
    )
    con.commit()
    con.close()
    logger.info(f"Created registration for user {user_id} with status '{status}'.")


def add_receipt_to_registration(user_id: int, receipt_file_id: str):
    """
    Finds the most recent pending registration for a user and adds the receipt file_id.
    """
    con = sqlite3.connect(DATABASE_NAME)
    cur = con.cursor()
    # We update the most recent pending registration that doesn't have a receipt yet.
    cur.execute(
        """
        UPDATE registrations
        SET receipt_file_id = ?
        WHERE registration_id = (
            SELECT registration_id FROM registrations
            WHERE user_id = ? AND status = 'pending_verification'
            ORDER BY registered_at DESC
            LIMIT 1
        )
        """,
        (receipt_file_id, user_id),
    )
    con.commit()
    con.close()
    logger.info(
        f"Added receipt {receipt_file_id} to latest pending registration for user {user_id}."
    )


def get_next_pending_registration():
    """Fetches the oldest pending registration for review that has a receipt."""
    con = sqlite3.connect(DATABASE_NAME)
    cur = con.cursor()
    cur.execute(
        """
        SELECT r.registration_id, r.user_id, r.receipt_file_id, u.username, u.first_name
        FROM registrations r
        JOIN users u ON r.user_id = u.user_id
        WHERE r.status = 'pending_verification' AND r.receipt_file_id IS NOT NULL
        ORDER BY r.registered_at ASC
        LIMIT 1
        """
    )
    result = cur.fetchone()
    con.close()
    return result


def update_registration_status(registration_id: int, new_status: str):
    """Updates the status of a specific registration."""
    con = sqlite3.connect(DATABASE_NAME)
    cur = con.cursor()
    cur.execute(
        "UPDATE registrations SET status = ? WHERE registration_id = ?",
        (new_status, registration_id),
    )
    con.commit()
    con.close()
    logger.info(f"Updated registration {registration_id} to status '{new_status}'.")
