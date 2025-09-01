import sqlite3
import logging
import secrets
from config import DATABASE_NAME

logger = logging.getLogger()


def init_db():
    """Initializes the database and adds new columns for the referral system."""
    try:
        con = sqlite3.connect(DATABASE_NAME)
        cur = con.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
                referral_code TEXT UNIQUE, invited_by_user_id INTEGER,
                referral_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # --- Add new columns if they don't exist (for backward compatibility) ---
        for col in ["referral_code", "invited_by_user_id", "referral_count"]:
            try:
                cur.execute(f"ALTER TABLE users ADD COLUMN {col}")
                if col == "referral_count":
                    cur.execute(
                        "UPDATE users SET referral_count = 0 WHERE referral_count IS NULL"
                    )
            except sqlite3.OperationalError:
                pass  # Column already exists

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
    """Adds a new user or updates info. Generates a referral code if one doesn't exist."""
    con = sqlite3.connect(DATABASE_NAME)
    cur = con.cursor()
    # Check if user exists
    cur.execute("SELECT referral_code FROM users WHERE user_id = ?", (user_id,))
    result = cur.fetchone()
    if not result or not result[0]:
        referral_code = secrets.token_urlsafe(6)
        cur.execute(
            """
            INSERT INTO users (user_id, username, first_name, referral_code) VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username,
                first_name=excluded.first_name,
                referral_code=COALESCE(users.referral_code, excluded.referral_code)
            """,
            (user_id, username, first_name, referral_code),
        )
    else:
        # Just update username and first name
        cur.execute(
            "UPDATE users SET username = ?, first_name = ? WHERE user_id = ?",
            (username, first_name, user_id),
        )
    con.commit()
    con.close()


def process_referral(inviter_code: str, new_user_id: int):
    """Processes a referral, linking the new user to the inviter."""
    con = sqlite3.connect(DATABASE_NAME)
    cur = con.cursor()
    # Find the inviter by their referral code
    cur.execute("SELECT user_id FROM users WHERE referral_code = ?", (inviter_code,))
    inviter = cur.fetchone()

    if inviter:
        inviter_id = inviter[0]
        # Link the new user to the inviter and increment the inviter's referral count
        cur.execute(
            "UPDATE users SET invited_by_user_id = ? WHERE user_id = ?",
            (inviter_id, new_user_id),
        )
        cur.execute(
            "UPDATE users SET referral_count = referral_count + 1 WHERE user_id = ?",
            (inviter_id,),
        )
        con.commit()
        logger.info(
            f"User {new_user_id} was successfully referred by user {inviter_id}."
        )
        return inviter_id
    con.close()
    return None


def get_user_referral_info(user_id: int):
    """Fetches a user's referral code and count."""
    con = sqlite3.connect(DATABASE_NAME)
    cur = con.cursor()
    cur.execute(
        "SELECT referral_code, referral_count FROM users WHERE user_id = ?", (user_id,)
    )
    result = cur.fetchone()
    con.close()
    return result


# --- Other database functions remain unchanged ---
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
    """Finds the most recent pending registration for a user and adds the receipt file_id."""
    con = sqlite3.connect(DATABASE_NAME)
    cur = con.cursor()
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
