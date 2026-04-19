import os
import sqlite3
import threading
import time
from app.storage.db import DB_PATH
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

ALLOWED_ROOT_DIRS = {"Projects", "Desktop", "Downloads", "Music", "Videos", "Documents", "Pictures"}
EXCLUDE_DIRS = {".cache", ".git", "node_modules", "__pycache__", ".venv", "venv", "env", ".local", ".config"}

def get_base_dirs():
    home = os.path.expanduser("~")
    dirs = []
    for folder_name in ALLOWED_ROOT_DIRS:
        base_path = os.path.join(home, folder_name)
        if os.path.isdir(base_path):
            dirs.append(base_path)
    return dirs

def _upsert_file(cursor, path):
    """Insert or update a single file in the DB without checking mtime first."""
    try:
        if any(exc in path for exc in EXCLUDE_DIRS):
            return
        size = os.path.getsize(path)
        mtime = os.path.getmtime(path)
        filename = os.path.basename(path)
        ext = os.path.splitext(filename)[1].lower()
        folder = os.path.dirname(path)

        # FTS5 does not support UNIQUE constraints or REPLACE by column.
        # We must explicitly delete the old record first.
        cursor.execute("DELETE FROM files WHERE path = ?", (path,))
        cursor.execute('''
            INSERT INTO files (filename, path, ext, folder, mtime, size)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (filename, path, ext, folder, mtime, size))
    except Exception:
        pass

def _delete_file(cursor, path):
    try:
        cursor.execute("DELETE FROM files WHERE path = ?", (path,))
    except Exception:
        pass

# --- FAST STARTUP SYNC ---

def build_index():
    """Ultra-fast initial sync. Preloads DB mtimes to avoid millions of SELECTs."""
    print("🚀 Starting fast DB sync...")
    start_t = time.time()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Preload existing DB state: path -> mtime
    cursor.execute("SELECT path, mtime FROM files")
    db_state = {row[0]: row[1] for row in cursor.fetchall()}
    indexed_paths = set()
    
    inserts = []
    
    for base_path in get_base_dirs():
        for root, dirs, files in os.walk(base_path):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for file in files:
                path = os.path.join(root, file)
                indexed_paths.add(path)
                
                try:
                    mtime = os.path.getmtime(path)
                    # Sync only if completely new, or modified
                    if path not in db_state or db_state[path] != mtime:
                        size = os.path.getsize(path)
                        filename = file
                        ext = os.path.splitext(filename)[1].lower()
                        inserts.append((filename, path, ext, root, mtime, size))
                except Exception:
                    continue

    # Bulk insert new/modified files
    if inserts:
        # Explicit delete required for FTS5 before inserting updates
        upsert_paths = [(i[1],) for i in inserts]
        cursor.executemany("DELETE FROM files WHERE path = ?", upsert_paths)
        
        cursor.executemany('''
            INSERT INTO files (filename, path, ext, folder, mtime, size)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', inserts)
        
    # Bulk delete paths that are no longer on disk
    deleted_paths = [(p,) for p in db_state.keys() if p not in indexed_paths]
    if deleted_paths:
        cursor.executemany("DELETE FROM files WHERE path = ?", deleted_paths)

    conn.commit()
    conn.close()
    
    print(f"✅ Sync complete in {time.time() - start_t:.2f}s! ({len(inserts)} ops, {len(indexed_paths)} total files)")

# --- WATCHDOG REALTIME SYNC ---

class SeekrEventHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        # Isolated connection for the watchdog daemon thread
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def on_created(self, event):
        if not event.is_directory:
            _upsert_file(self.cursor, event.src_path)
            self.conn.commit()

    def on_modified(self, event):
        if not event.is_directory:
            _upsert_file(self.cursor, event.src_path)
            self.conn.commit()

    def on_deleted(self, event):
        if not event.is_directory:
            _delete_file(self.cursor, event.src_path)
            self.conn.commit()

    def on_moved(self, event):
        if not event.is_directory:
            _delete_file(self.cursor, event.src_path)
            _upsert_file(self.cursor, event.dest_path)
            self.conn.commit()

def start_watchdog():
    """Start the realtime file watcher daemon."""
    event_handler = SeekrEventHandler()
    observer = Observer()
    
    for base_path in get_base_dirs():
        observer.schedule(event_handler, base_path, recursive=True)
        
    observer.start()
    print("👀 Watchdog daemon started. Listening for file changes...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()