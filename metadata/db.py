import sqlite3
import os
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(__file__), 'fs.db')

def get_connection():
    return sqlite3.connect(DB_FILE)

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        with open(schema_path, 'r') as f:
            cursor.executescript(f.read())
        conn.commit()

def upsert_metadata(path, name, size):
    last_modified = int(os.path.getmtime(path))  # Get file's last modified UNIX timestamp

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO file_metadata (path, name, size, last_modified)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                size = excluded.size,
                last_modified = excluded.last_modified
        ''', (path, name, size, last_modified))
        conn.commit()


def fetch_all_metadata():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM file_metadata')
        return cursor.fetchall()
