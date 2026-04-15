import os
import sqlite3
from app.storage.db import DB_PATH

# Folders to scan
ALLOWED_ROOT_DIRS = {"Projects", "Desktop", "Downloads", "Music", "Videos", "Documents"}
# Folders to ignore inside traversal
EXCLUDE_DIRS = {".cache", ".git", "node_modules", "__pycache__", ".venv", "venv", "env", ".local", ".config"}

# File types whose text content will be indexed for full-text search
TEXT_EXTENSIONS = {
    ".py", ".txt", ".md", ".js", ".ts", ".html", ".css", ".json",
    ".yaml", ".yml", ".xml", ".sh", ".conf", ".ini", ".cfg", ".toml",
    ".csv", ".rs", ".go", ".c", ".cpp", ".h", ".java", ".rb", ".php",
    ".jsx", ".tsx", ".vue", ".sql", ".r", ".kt", ".swift",
}

# Maximum file size to read content from (512 KB)
SIZE_LIMIT_BYTES = 512 * 1024


def _read_content(path: str, size: int) -> str:
    """Read file content for indexing. Returns empty string for binary/large files."""
    ext = os.path.splitext(path)[1].lower()
    if ext not in TEXT_EXTENSIONS or size > SIZE_LIMIT_BYTES:
        return ""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


def build_index():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    home = os.path.expanduser("~")
    indexed_paths = set()  # Track what we saw during this scan

    for folder_name in ALLOWED_ROOT_DIRS:
        base_path = os.path.join(home, folder_name)
        if not os.path.exists(base_path):
            continue

        for root, dirs, files in os.walk(base_path):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

            for file in files:
                path = os.path.join(root, file)
                indexed_paths.add(path)

                try:
                    mtime = os.path.getmtime(path)
                    size  = os.path.getsize(path)

                    # Smart skip: only reindex if mtime changed
                    cursor.execute("SELECT mtime FROM files WHERE path = ?", (path,))
                    result = cursor.fetchone()
                    if result and result[0] == mtime:
                        continue

                    ext     = os.path.splitext(file)[1].lower()
                    content = _read_content(path, size)

                    cursor.execute('''
                        INSERT OR REPLACE INTO files (filename, path, ext, folder, content, mtime, size)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (file, path, ext, root, content, mtime, size))

                except Exception:
                    continue

    conn.commit()

    # Cleanup: remove DB entries for files deleted from disk
    cursor.execute("SELECT path FROM files")
    db_paths = [row[0] for row in cursor.fetchall()]

    deleted_paths = [p for p in db_paths if p not in indexed_paths]
    if deleted_paths:
        cursor.executemany("DELETE FROM files WHERE path = ?", [(p,) for p in deleted_paths])
        conn.commit()

    conn.close()
    print(f"✅ Smart Sync Complete! Indexed {len(indexed_paths)} files.")