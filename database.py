import sqlite3
import uuid
from datetime import datetime
from config import DATABASE_NAME

# --- Schema Definition ---
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    referral_code TEXT UNIQUE,
    invited_by_user_id INTEGER,
    referral_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    date TEXT,
    reminders TEXT, -- e.g., "24,1" for 24 hours and 1 hour before
    is_active INTEGER DEFAULT 1, -- 1 for true, 0 for false
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS registrations (
    registration_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    event_id INTEGER,
    status TEXT, -- e.g., 'pending_verification', 'confirmed', 'rejected'
    receipt_file_id TEXT,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id),
    FOREIGN KEY (event_id) REFERENCES events (event_id)
);
"""


def get_db_connection():
    """Establishes a connection to the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    """Creates the database tables if they don't already exist."""
    conn = get_db_connection()
    conn.executescript(SCHEMA)
    conn.close()


# --- User Functions ---
def add_or_update_user(user_id, username, first_name, invited_by=None):
    """Adds a new user or updates their info if they already exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if user is None:
        referral_code = str(uuid.uuid4())[:8]
        cursor.execute(
            "INSERT INTO users (user_id, username, first_name, referral_code, invited_by_user_id) VALUES (?, ?, ?, ?, ?)",
            (user_id, username, first_name, referral_code, invited_by),
        )
        if invited_by:
            cursor.execute(
                "UPDATE users SET referral_count = referral_count + 1 WHERE user_id = ?",
                (invited_by,),
            )
    else:
        cursor.execute(
            "UPDATE users SET username = ?, first_name = ? WHERE user_id = ?",
            (username, first_name, user_id),
        )
    conn.commit()
    conn.close()


def find_user_by_referral_code(code):
    """Finds a user's ID by their referral code."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE referral_code = ?", (code,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def get_user_referral_info(user_id):
    """Gets a user's referral code and count."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT referral_code, referral_count FROM users WHERE user_id = ?",
        (user_id,),
    )
    result = cursor.fetchone()
    conn.close()
    return result


# --- Registration Functions ---
def create_registration(user_id, event_id, status, receipt_file_id=None):
    """Creates a new registration record."""
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO registrations (user_id, event_id, status, receipt_file_id) VALUES (?, ?, ?, ?)",
        (user_id, event_id, status, receipt_file_id),
    )
    conn.commit()
    conn.close()


def get_next_pending_registration():
    """Fetches the oldest pending registration that has a receipt."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT r.registration_id, r.user_id, r.receipt_file_id, u.username, u.first_name, e.name
        FROM registrations r
        JOIN users u ON r.user_id = u.user_id
        JOIN events e ON r.event_id = e.event_id
        WHERE r.status = 'pending_verification' AND r.receipt_file_id IS NOT NULL
        ORDER BY r.registered_at ASC
        LIMIT 1
    """
    )
    result = cursor.fetchone()
    conn.close()
    return result


def update_registration_status(registration_id, new_status):
    """Updates the status of a specific registration."""
    conn = get_db_connection()
    conn.execute(
        "UPDATE registrations SET status = ? WHERE registration_id = ?",
        (new_status, registration_id),
    )
    conn.commit()
    conn.close()


def add_receipt_to_registration(user_id, event_id, receipt_file_id):
    """Adds a receipt file ID to a user's pending registration for a specific event."""
    conn = get_db_connection()
    conn.execute(
        """
        UPDATE registrations
        SET receipt_file_id = ?
        WHERE user_id = ? AND event_id = ? AND status = 'pending_verification'
        """,
        (receipt_file_id, user_id, event_id),
    )
    conn.commit()
    conn.close()


def get_confirmed_attendees(event_id):
    """Gets a list of user IDs for confirmed attendees of an event."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id FROM registrations WHERE event_id = ? AND status = 'confirmed'",
        (event_id,),
    )
    attendees = [row[0] for row in cursor.fetchall()]
    conn.close()
    return attendees


# --- Event Functions ---
def get_active_event():
    """Gets the currently active event."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events WHERE is_active = 1 LIMIT 1")
    event = cursor.fetchone()
    conn.close()
    return event


def create_event(name, date, reminders):
    """Creates a new event and sets it as the only active one."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Deactivate all other events first
    cursor.execute("UPDATE events SET is_active = 0")
    # Insert the new event
    cursor.execute(
        "INSERT INTO events (name, date, reminders, is_active) VALUES (?, ?, ?, 1)",
        (name, date, reminders),
    )
    conn.commit()
    conn.close()


def get_all_events():
    """Fetches all events from the database, newest first."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events ORDER BY created_at DESC")
    events = cursor.fetchall()
    conn.close()
    return events


def get_events_with_pending_reminders():
    """Finds events that have reminders due to be sent."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events WHERE is_active = 1 AND date IS NOT NULL")
    events = cursor.fetchall()
    conn.close()
    return events
