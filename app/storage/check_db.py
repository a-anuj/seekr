import sqlite3
import os

DB_PATH = os.path.expanduser("~/.local/share/seekr/seekr.db")

def preview_db():
    if not os.path.exists(DB_PATH):
        print("Database file not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get the total count of indexed files
    cursor.execute("SELECT COUNT(*) FROM files")
    count = cursor.fetchone()[0]
    print(f"Total files indexed: {count}")
    print("-" * 50)

    # Fetch the top 10 most recent files
    cursor.execute("SELECT filename, folder, ext, mtime FROM files LIMIT 10")
    rows = cursor.fetchall()

    for row in rows:
        print(f"File: {row[0]}")
        print(f"Folder: {row[1]}")
        print(f"Ext: {row[2]}")
        print(f"Timestamp: {row[3]}")
        print("-" * 30)

    conn.close()

if __name__ == "__main__":
    preview_db()