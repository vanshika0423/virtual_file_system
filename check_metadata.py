from datetime import datetime
from metadata.db import get_connection

def fetch_metadata():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT name, size, path, last_modified FROM file_metadata')
        rows = cursor.fetchall()

    metadata = []
    for name, size, path, last_modified in rows:
        readable_date = (
            datetime.fromtimestamp(last_modified).strftime('%Y-%m-%d %H:%M:%S')
            if last_modified else 'N/A'
        )
        metadata.append({
            'name': name,
            'size': size,
            'path': path,
            'last_modified': readable_date
        })
    return metadata

if __name__ == '__main__':
    data = fetch_metadata()
    if not data:
        print("No metadata found.")
    else:
        for entry in data:
            print(entry)
