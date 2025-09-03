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
    description TEXT,
    date TEXT,
    fee REAL DEFAULT 0.0,
    is_paid INTEGER DEFAULT 0,
    payment_details TEXT,
    reminders TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS discount_codes (
    code_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    code TEXT NOT NULL,
    discount_type TEXT NOT NULL, -- 'percentage' or 'fixed'
    value REAL NOT NULL,
    uses_left INTEGER DEFAULT 1,
    is_active INTEGER DEFAULT 1,
    UNIQUE(event_id, code),
    FOREIGN KEY (event_id) REFERENCES events (event_id)
);

CREATE TABLE IF NOT EXISTS registrations (
    registration_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    event_id INTEGER,
    status TEXT,
    ticket_code TEXT UNIQUE,
    receipt_file_id TEXT,
    discount_code_used TEXT,
    final_fee REAL,
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
    """Creates the database tables and adds new columns if they don't already exist."""
    conn = get_db_connection()
    conn.executescript(SCHEMA)
    # --- Add new columns for backward compatibility ---
    try:
        conn.execute("ALTER TABLE events ADD COLUMN fee REAL DEFAULT 0.0")
        conn.execute("ALTER TABLE registrations ADD COLUMN discount_code_used TEXT")
        conn.execute("ALTER TABLE registrations ADD COLUMN final_fee REAL")
    except sqlite3.OperationalError:
        pass  # Columns already exist
    conn.close()


# --- User Functions (Unchanged) ---
def add_or_update_user(user_id, username, first_name, invited_by=None):
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
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE referral_code = ?", (code,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def get_user_referral_info(user_id):
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
def create_registration(user_id, event_id, status, final_fee=None, discount_code=None):
    """Creates a new registration record, including fee and discount info."""
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO registrations (user_id, event_id, status, final_fee, discount_code_used) VALUES (?, ?, ?, ?, ?)",
        (user_id, event_id, status, final_fee, discount_code),
    )
    conn.commit()
    conn.close()


def get_last_registration_id(user_id: int, event_id: int) -> int | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT registration_id FROM registrations WHERE user_id = ? AND event_id = ? ORDER BY registered_at DESC LIMIT 1",
        (user_id, event_id),
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def get_next_pending_registration():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT r.registration_id, r.user_id, r.receipt_file_id, u.username, u.first_name, e.name, r.final_fee, r.discount_code_used
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
    conn = get_db_connection()
    ticket_code = None
    if new_status == "confirmed":
        ticket_code = str(uuid.uuid4()).split("-")[0].upper()
        conn.execute(
            "UPDATE registrations SET status = ?, ticket_code = ? WHERE registration_id = ?",
            (new_status, ticket_code, registration_id),
        )
    else:
        conn.execute(
            "UPDATE registrations SET status = ? WHERE registration_id = ?",
            (new_status, registration_id),
        )
    conn.commit()
    conn.close()
    return ticket_code


def add_receipt_to_registration(user_id, event_id, receipt_file_id):
    conn = get_db_connection()
    conn.execute(
        """
        UPDATE registrations SET receipt_file_id = ?
        WHERE user_id = ? AND event_id = ? AND status = 'pending_verification'
        """,
        (receipt_file_id, user_id, event_id),
    )
    conn.commit()
    conn.close()


def get_confirmed_attendees(event_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id FROM registrations WHERE event_id = ? AND status = 'confirmed'",
        (event_id,),
    )
    attendees = [row[0] for row in cursor.fetchall()]
    conn.close()
    return attendees


def get_participants_for_event(event_id: int):
    """Fetches a list of participants for a given event."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT u.username, r.discount_code_used
        FROM registrations r
        JOIN users u ON r.user_id = u.user_id
        WHERE r.event_id = ? AND r.status = 'confirmed'
        ORDER BY r.registered_at
    """,
        (event_id,),
    )
    participants = cursor.fetchall()
    conn.close()
    return participants


# --- Event Functions ---
def get_active_event():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events WHERE is_active = 1 LIMIT 1")
    event = cursor.fetchone()
    conn.close()
    return event


def create_event(name, description, date, fee, is_paid, payment_details, reminders):
    """Creates a new event with detailed information."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE events SET is_active = 0")
    cursor.execute(
        """
        INSERT INTO events (name, description, date, fee, is_paid, payment_details, reminders, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """,
        (name, description, date, fee, is_paid, payment_details, reminders),
    )
    conn.commit()
    conn.close()


def get_all_events():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events ORDER BY created_at DESC")
    events = cursor.fetchall()
    conn.close()
    return events


def get_events_with_pending_reminders():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events WHERE is_active = 1 AND date IS NOT NULL")
    events = cursor.fetchall()
    conn.close()
    return events


def get_event_by_id(event_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events WHERE event_id = ?", (event_id,))
    event = cursor.fetchone()
    conn.close()
    return event


def set_active_event(event_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE events SET is_active = 0")
    cursor.execute("UPDATE events SET is_active = 1 WHERE event_id = ?", (event_id,))
    conn.commit()
    conn.close()


def delete_event_by_id(event_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("BEGIN TRANSACTION")
    try:
        cursor.execute("DELETE FROM registrations WHERE event_id = ?", (event_id,))
        cursor.execute("DELETE FROM discount_codes WHERE event_id = ?", (event_id,))
        cursor.execute("DELETE FROM events WHERE event_id = ?", (event_id,))
        cursor.execute("COMMIT")
    except sqlite3.Error:
        cursor.execute("ROLLBACK")
        raise
    finally:
        conn.close()


# --- Discount Code Functions ---
def create_discount_code(event_id, code, discount_type, value, uses_left):
    """Creates a new discount code for a specific event."""
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO discount_codes (event_id, code, discount_type, value, uses_left) VALUES (?, ?, ?, ?, ?)",
        (event_id, code, discount_type, value, uses_left),
    )
    conn.commit()
    conn.close()


def get_discount_code(event_id: int, code: str):
    """Validates and retrieves a discount code for a specific event."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM discount_codes WHERE event_id = ? AND code = ? AND is_active = 1 AND uses_left > 0",
        (event_id, code),
    )
    discount = cursor.fetchone()
    conn.close()
    return discount


def use_discount_code(code_id: int):
    """Decrements the use count of a discount code."""
    conn = get_db_connection()
    conn.execute(
        "UPDATE discount_codes SET uses_left = uses_left - 1 WHERE code_id = ?",
        (code_id,),
    )
    conn.commit()
    conn.close()
