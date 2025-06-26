CREATE TABLE IF NOT EXISTS file_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    size INTEGER,
    created_at TIMESTAMP DEFAULT (datetime('now', '+5 hours', '+30 minutes')),
    updated_at TIMESTAMP DEFAULT (datetime('now', '+5 hours', '+30 minutes')),
    last_modified INTEGER
);

CREATE TRIGGER IF NOT EXISTS update_file_metadata_timestamp
AFTER UPDATE ON file_metadata
FOR EACH ROW
BEGIN
    UPDATE file_metadata
    SET updated_at = datetime('now', '+5 hours', '+30 minutes')
    WHERE id = OLD.id;
END;
