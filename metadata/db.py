import sqlite3
import os

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
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO file_metadata (path, name, size)
            VALUES (?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                size = excluded.size
        ''', (path, name, size))
        conn.commit()

def fetch_all_metadata():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM file_metadata')
        rows = cursor.fetchall()
        print(f"DEBUG: fetched {len(rows)} rows from DB")
        return rows

