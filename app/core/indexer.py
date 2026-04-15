import os
import sqlite3
from app.storage.db import DB_PATH

# Folders to scan
ALLOWED_ROOT_DIRS = {"Projects", "Desktop", "Downloads", "Music", "Videos", "Documents"}
# Folders to ignore inside traversal
EXCLUDE_DIRS = {".cache", ".git", "node_modules", "__pycache__", ".venv", "venv", "env", ".local", ".config"}

def build_index():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 🛑 REMOVED: cursor.execute("DELETE FROM files") 
    # We no longer wipe the DB on start.

    home = os.path.expanduser("~")
    indexed_paths = set() # To keep track of what we saw during this scan

    for folder_name in ALLOWED_ROOT_DIRS:
        base_path = os.path.join(home, folder_name)
        if not os.path.exists(base_path):
            continue
            
        for root, dirs, files in os.walk(base_path):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for file in files:
                path = os.path.join(root, file)
                indexed_paths.add(path) # Mark this file as 'still exists'
                
                try:
                    mtime = os.path.getmtime(path)
                    
                    # 🚀 SMART MOVE: Check if we already have this file with the same mtime
                    cursor.execute("SELECT mtime FROM files WHERE path = ?", (path,))
                    result = cursor.fetchone()
                    
                    if result and result[0] == mtime:
                        continue # Skip this file! Nothing has changed.
                    
                    # If file is new or modified, Update/Insert it
                    ext = os.path.splitext(file)[1].lower()
                    cursor.execute('''
                        INSERT OR REPLACE INTO files (filename, path, ext, folder, mtime)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (file, path, ext, root, mtime))
                    
                except Exception:
                    continue
    
    conn.commit()

    # 🧹 CLEANUP: Remove files from DB that were deleted from the disk
    # (i.e., they are in the DB but were NOT seen in our indexed_paths set)
    cursor.execute("SELECT path FROM files")
    db_paths = [row[0] for row in cursor.fetchall()]
    
    deleted_paths = [p for p in db_paths if p not in indexed_paths]
    if deleted_paths:
        cursor.executemany("DELETE FROM files WHERE path = ?", [(p,) for p in deleted_paths])
        conn.commit()

    conn.close()
    print("✅ Smart Sync Complete!")