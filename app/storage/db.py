import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.expanduser("~/.local/share/seekr/seekr.db")

# Schema version — bump this whenever column layout changes
_SCHEMA_VERSION = 2

def _needs_migration(cursor):
    """Return True if the live table is missing the content or size column."""
    try:
        # fts5 tables report their schema via fts5_tokenize pragma trick;
        # simplest check: just try to read a known new column.
        cursor.execute("SELECT content, size FROM files LIMIT 1")
        return False
    except sqlite3.OperationalError:
        return True

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Enable WAL for simultaneous read/write
    cursor.execute("PRAGMA journal_mode=WAL;")

    # Schema migration: if the table exists but is missing content/size, drop and rebuild.
    # The background indexer will repopulate it on the next startup.
    if _needs_migration(cursor):
        print("🔄 DB schema upgrade detected — rebuilding index table...")
        cursor.execute("DROP TABLE IF EXISTS files")

    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS files USING fts5(
            filename,
            path,
            ext,
            folder,
            content,
            mtime    UNINDEXED,
            size     UNINDEXED
        )
    ''')
    conn.commit()
    conn.close()


def _format_snippet(raw: str) -> str:
    """
    FTS5 snippet() uses \x02 / \x03 as open/close bold markers.
    Convert to a plain string with ** markers for the UI layer to bold.
    """
    return raw.replace("\x02", "**").replace("\x03", "**")


def search_db(filters: dict):
    """
    Returns a list of (path, snippet_or_None, size_bytes) tuples,
    sorted by relevance (mtime or size depending on filters).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    is_content_search = bool(filters.get("content") and filters["content"].strip())

    # Choose SELECT columns based on whether we need a snippet
    if is_content_search:
        # snippet(table, column_index, open_marker, close_marker, ellipsis, tokens)
        # content is column index 4 in our schema (0-based)
        select = "SELECT path, snippet(files, 4, '\x02', '\x03', '...', 12), size FROM files"
    else:
        select = "SELECT path, NULL, size FROM files"

    where = " WHERE 1=1"
    params = []

    # 1. Name / keyword search — scoped to filename + path columns only.
    # Skip if `name` is identical to `folder`: the folder LIKE filter already
    # handles the directory constraint; adding a redundant FTS5 MATCH would
    # exclude files whose *filenames* don't contain the folder name (e.g.
    # vacation.jpg inside ~/Pictures would be dropped).
    name_val = (filters.get("name") or "").strip()
    folder_val = (filters.get("folder") or "").strip()
    if name_val and name_val.lower() != folder_val.lower():
        # Scope to filename and path columns (indices 0 and 1) so we don't
        # accidentally match on unrelated content / extension tokens.
        where += " AND rowid IN (SELECT rowid FROM files WHERE files MATCH ?)"
        params.append(f"{{filename path}} : {name_val}*")

    # 2. Content search (FTS5 scoped to the content column)
    if is_content_search:
        where += " AND rowid IN (SELECT rowid FROM files WHERE files MATCH ?)"
        params.append(f"content : {filters['content']}")

    # 3. Extension filter
    if filters.get("ext"):
        ext = filters["ext"] if filters["ext"].startswith(".") else f".{filters['ext']}"
        where += " AND LOWER(ext) = LOWER(?)"
        params.append(ext)

    # 4. Folder filter
    if filters.get("folder"):
        where += " AND folder LIKE ?"
        params.append(f"%{filters['folder']}%")

    # 5. Time filter
    if filters.get("time"):
        start, end = filters["time"]
        if isinstance(start, datetime):
            start = start.timestamp()
        if isinstance(end, datetime):
            end = end.timestamp()
        where += " AND mtime >= ? AND mtime <= ?"
        params.extend([start, end])

    # 6. Size range filters
    if filters.get("size_min") is not None:
        where += " AND size >= ?"
        params.append(filters["size_min"])
    if filters.get("size_max") is not None:
        where += " AND size <= ?"
        params.append(filters["size_max"])

    # 7. Order: size_sort overrides default mtime ordering
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
        # rows: [(path, snippet_or_None, size), ...]
        results = [
            (row[0], _format_snippet(row[1]) if row[1] else None, row[2])
            for row in rows
        ]
    except Exception as e:
        print(f"SQL Error: {e}")
        results = []
    finally:
        conn.close()

    return results