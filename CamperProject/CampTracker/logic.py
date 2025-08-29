"""Logic for the Camper Information Management System."""

import sqlite3
import os
import shutil
from datetime import datetime
from models import UserData


def get_db_path():
    return os.path.join(os.path.dirname(__file__), "campers.db")


def init_db():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS campers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            surname TEXT NOT NULL,
            email TEXT,
            number TEXT UNIQUE,
            note TEXT,
            rating REAL,
            status TEXT
        )
    """
    )
    conn.commit()
    conn.close()


# Call this at import to ensure DB exists
init_db()


def clear_entries(
    name_entry,
    surname_entry,
    email_entry,
    number_entry,
    note_entry,
    rating_var,
    status_var,
):
    """Clear the input fields."""
    name_entry.delete(0, "end")
    surname_entry.delete(0, "end")
    email_entry.delete(0, "end")
    number_entry.delete(0, "end")
    note_entry.delete("1.0", "end")  # For Text widget
    rating_var.set(0)  # Reset rating
    status_var.set("")


def handle_submit(
    name_entry,
    surname_entry,
    email_entry,
    number_entry,
    note_entry,
    rating_var,
    status_var,
):
    """Handle the submit button click."""
    name = name_entry.get()
    surname = surname_entry.get()
    email = email_entry.get()
    number = number_entry.get()
    note = note_entry.get("1.0", "end-1c")  # Get text without trailing newline
    rating = rating_var.get()
    status = status_var.get()

    user = UserData(name, number, surname, note, rating, email, status)
    if user.is_valid():
        add_camper(user)
        clear_entries(
            name_entry,
            surname_entry,
            email_entry,
            number_entry,
            note_entry,
            rating_var,
            status_var,
        )


def add_camper(user: UserData):
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO campers (name, surname, email, number, note, rating, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            user.name,
            user.surname,
            user.email,
            user.number,
            user.note,
            user.rating,
            user.status,
        ),
    )
    conn.commit()
    conn.close()


def update_camper(camper_id, user: UserData):
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        """
        UPDATE campers SET name=?, surname=?, email=?, number=?, note=?, rating=?, status=? WHERE id=?
    """,
        (
            user.name,
            user.surname,
            user.email,
            user.number,
            user.note,
            user.rating,
            user.status,
            camper_id,
        ),
    )
    conn.commit()
    conn.close()


def fetch_campers(search_term=None, column=None):
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    query = "SELECT id, name, surname, email, number, note, rating, status FROM campers"
    params = []
    if search_term and column:
        query += f" WHERE {column} LIKE ?"
        params.append(f"%{search_term}%")
    campers = []
    for row in c.execute(query, params):
        campers.append(
            {
                "id": row[0],
                "name": row[1],
                "surname": row[2],
                "email": row[3],
                "number": row[4],
                "note": row[5],
                "rating": row[6],
                "status": row[7],
            }
        )
    conn.close()
    return campers


def delete_camper(camper_id):
    """Delete a camper by their unique id."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("DELETE FROM campers WHERE id=?", (camper_id,))
    conn.commit()
    conn.close()


def delete_camper_by_number(number):
    """Delete a camper by their unique number."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("DELETE FROM campers WHERE number=?", (number,))
    conn.commit()
    conn.close()


def save_all_campers(items):
    """Save function for in-line edits with duplicate prevention on number and email"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    for item in items:
        camper_id = item.get("id", None)

        if camper_id:
            # Update existing record
            c.execute(
                """
                UPDATE campers
                SET name=?, surname=?, email=?, number=?, note=?, rating=?, status=?
                WHERE id=?
                """,
                (
                    item.get("name", ""),
                    item.get("surname", ""),
                    item.get("email", ""),
                    item.get("number", ""),
                    item.get("note", ""),
                    float(item.get("rating", 0)),
                    item.get("status", ""),
                    camper_id,
                ),
            )
        else:
            # Insert new, ignore if email or number exists
            try:
                c.execute(
                    """
                    INSERT OR IGNORE INTO campers
                    (name, surname, email, number, note, rating, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item.get("name", ""),
                        item.get("surname", ""),
                        item.get("email", ""),
                        item.get("number", ""),
                        item.get("note", ""),
                        float(item.get("rating", 0)),
                        item.get("status", ""),
                    ),
                )
            except sqlite3.IntegrityError as e:
                print(f"Insert failed for number {item.get('number')}: {e}")

    conn.commit()
    conn.close()

def get_backup_dir():
    backup_dir = os.path.join(os.path.dirname(__file__), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir

def create_db_backup():
    """Create a timestamped backup of the campers.db file."""

    db_path = get_db_path()
    if not os.path.exists(db_path):
        raise FileNotFoundError("Database file not found.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"campers_backup_{timestamp}.db"
    backup_path = os.path.join(get_backup_dir(), backup_name)

    shutil.copy2(db_path, backup_path)
    return backup_path  # return path for UI confirmation