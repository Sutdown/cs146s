"""
Database layer for the Action Item Extractor application.
Handles all database operations with proper error handling.
"""
from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "app.db"


# ============================================================================
# Database Initialization
# ============================================================================

def ensure_data_directory_exists() -> None:
    """Ensure the data directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def init_db() -> None:
    """
    Initialize the database with required tables.
    Creates notes and action_items tables if they don't exist.
    """
    ensure_data_directory_exists()
    logger.info("Initializing database...")

    with get_connection() as connection:
        cursor = connection.cursor()

        # Create notes table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );
            """
        )

        # Create action_items table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS action_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                note_id INTEGER,
                text TEXT NOT NULL,
                done INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (note_id) REFERENCES notes(id)
            );
            """
        )

        connection.commit()
        logger.info("Database initialized successfully")


# ============================================================================
# Connection Management
# ============================================================================

@contextmanager
def get_connection():
    """
    Context manager for database connections.
    Ensures proper cleanup of connections.
    """
    ensure_data_directory_exists()
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


# ============================================================================
# Note Operations
# ============================================================================

def insert_note(content: str) -> int:
    """
    Insert a new note into the database.

    Args:
        content: The note content.

    Returns:
        The ID of the inserted note.

    Raises:
        sqlite3.Error: If the insertion fails.
    """
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO notes (content) VALUES (?)", (content,))
            connection.commit()
            note_id = int(cursor.lastrowid)
            logger.info(f"Inserted note with id={note_id}")
            return note_id
    except sqlite3.Error as e:
        logger.error(f"Failed to insert note: {e}")
        raise


def get_note(note_id: int) -> Optional[dict]:
    """
    Get a note by its ID.

    Args:
        note_id: The ID of the note to retrieve.

    Returns:
        A dictionary with note data, or None if not found.
    """
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT id, content, created_at FROM notes WHERE id = ?",
                (note_id,),
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    except sqlite3.Error as e:
        logger.error(f"Failed to get note {note_id}: {e}")
        raise


def list_notes() -> list[dict]:
    """
    List all notes, ordered by most recent first.

    Returns:
        A list of note dictionaries.
    """
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id, content, created_at FROM notes ORDER BY id DESC")
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Failed to list notes: {e}")
        raise


def delete_note(note_id: int) -> bool:
    """
    Delete a note by its ID.

    Args:
        note_id: The ID of the note to delete.

    Returns:
        True if the note was deleted, False if not found.
    """
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            connection.commit()
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Deleted note with id={note_id}")
            return deleted
    except sqlite3.Error as e:
        logger.error(f"Failed to delete note {note_id}: {e}")
        raise


# ============================================================================
# Action Item Operations
# ============================================================================

def insert_action_items(items: list[str], note_id: Optional[int] = None) -> list[int]:
    """
    Insert multiple action items into the database.

    Args:
        items: List of action item texts.
        note_id: Optional ID of the associated note.

    Returns:
        List of inserted item IDs.

    Raises:
        sqlite3.Error: If insertion fails.
    """
    if not items:
        return []

    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            ids: list[int] = []

            for item in items:
                cursor.execute(
                    "INSERT INTO action_items (note_id, text) VALUES (?, ?)",
                    (note_id, item),
                )
                ids.append(int(cursor.lastrowid))

            connection.commit()
            logger.info(f"Inserted {len(ids)} action items")
            return ids
    except sqlite3.Error as e:
        logger.error(f"Failed to insert action items: {e}")
        raise


def list_action_items(note_id: Optional[int] = None) -> list[dict]:
    """
    List action items, optionally filtered by note ID.

    Args:
        note_id: Optional filter by note ID.

    Returns:
        A list of action item dictionaries.
    """
    try:
        with get_connection() as connection:
            cursor = connection.cursor()

            if note_id is None:
                cursor.execute(
                    "SELECT id, note_id, text, done, created_at FROM action_items ORDER BY id DESC"
                )
            else:
                cursor.execute(
                    "SELECT id, note_id, text, done, created_at FROM action_items WHERE note_id = ? ORDER BY id DESC",
                    (note_id,),
                )

            rows = cursor.fetchall()
            # Convert done (0/1) to bool for consistency
            result = []
            for row in rows:
                item = dict(row)
                item["done"] = bool(item["done"])
                result.append(item)
            return result
    except sqlite3.Error as e:
        logger.error(f"Failed to list action items: {e}")
        raise


def mark_action_item_done(action_item_id: int, done: bool) -> None:
    """
    Mark an action item as done or not done.

    Args:
        action_item_id: The ID of the action item.
        done: Whether to mark as done.

    Raises:
        sqlite3.Error: If the update fails.
    """
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE action_items SET done = ? WHERE id = ?",
                (1 if done else 0, action_item_id),
            )
            connection.commit()
            logger.info(f"Marked action item {action_item_id} as done={done}")
    except sqlite3.Error as e:
        logger.error(f"Failed to mark action item {action_item_id}: {e}")
        raise
