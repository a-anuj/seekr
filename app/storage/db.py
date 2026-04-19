import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.expanduser("~/.local/share/seekr/seekr.db")

def _needs_migration(cursor):
    """Return True if the live table has the deprecated 'content' column."""
    try:
        cursor.execute("SELECT content FROM files LIMIT 1")
        return True
    except sqlite3.OperationalError:
        return False

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Enable WAL for simultaneous read/write
    cursor.execute("PRAGMA journal_mode=WAL;")

    # Schema migration: if the table has the old content col, drop and rebuild.
    if _needs_migration(cursor):
        print("🔄 DB schema upgrade detected — removing content index...")
        cursor.execute("DROP TABLE IF EXISTS files")

    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS files USING fts5(
            filename,
            path,
            ext,
            folder,
            mtime    UNINDEXED,
            size     UNINDEXED
        )
    ''')
    conn.commit()
    conn.close()

def search_db(filters: dict):
    """
    Returns a list of (path, None, size_bytes) tuples,
    sorted by relevance (mtime or size depending on filters).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    select = "SELECT path, NULL, size FROM files"
    where = " WHERE 1=1"
    params = []

    # 1. Name / keyword search
    name_val = (filters.get("name") or "").strip()
    folder_val = (filters.get("folder") or "").strip()
    if name_val and name_val.lower() != folder_val.lower():
        where += " AND files MATCH ?"
        params.append(f"{{filename path}} : {name_val}*")

    # 2. Extension filter
    if filters.get("ext"):
        ext = filters["ext"] if filters["ext"].startswith(".") else f".{filters['ext']}"
        where += " AND LOWER(ext) = LOWER(?)"
        params.append(ext)

    # 3. Folder filter
    if filters.get("folder"):
        where += " AND folder LIKE ?"
        params.append(f"%{filters['folder']}%")

    # 4. Time filter
    if filters.get("time"):
        start, end = filters["time"]
        if isinstance(start, datetime):
            start = start.timestamp()
        if isinstance(end, datetime):
            end = end.timestamp()
        where += " AND mtime >= ? AND mtime <= ?"
        params.extend([start, end])

    # 5. Size range filters
    if filters.get("size_min") is not None:
        where += " AND size >= ?"
        params.append(filters["size_min"])
    if filters.get("size_max") is not None:
        where += " AND size <= ?"
        params.append(filters["size_max"])

    # 6. Order: size_sort overrides default mtime ordering
    size_sort = filters.get("size_sort")
    if size_sort == "desc":
        order = " ORDER BY size DESC"
    elif size_sort == "asc":
        order = " ORDER BY size ASC"
    else:
        order = " ORDER BY mtime DESC"

    full_query = select + where + order + " LIMIT 50"

    try:
        cursor.execute(full_query, params)
        rows = cursor.fetchall()
        # rows: [(path, None, size), ...]
        results = [
            (row[0], None, row[2])
            for row in rows
        ]
    except Exception as e:
        print(f"SQL Error: {e}")
        results = []
    finally:
        conn.close()

    return results