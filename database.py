import sqlite3
import os

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'voting_system.db')

def get_db_connection():
    """Establishes and returns a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys constraint enforcement in SQLite
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def execute_query(query, params=()):
    """Executes a write query (INSERT, UPDATE, DELETE) and commits changes.
    Returns the last inserted row ID.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        conn.commit()
        last_id = cursor.lastrowid
        return last_id
    except sqlite3.Error as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def execute_read_query(query, params=()):
    """Executes a read query (SELECT) and returns list of dictionaries representing the rows."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        raise e
    finally:
        conn.close()

def execute_read_one(query, params=()):
    """Executes a read query (SELECT) and returns a single dictionary representing the row, or None."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.Error as e:
        raise e
    finally:
        conn.close()
