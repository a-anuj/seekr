import os
import sqlite3
from storage.db import DB_PATH

# Folders to scan
ALLOWED_ROOT_DIRS = {"Projects", "Desktop", "Downloads", "Music", "Videos", "Documents"}
# Folders to ignore inside traversal
EXCLUDE_DIRS = {".cache", ".git", "node_modules", "__pycache__", ".venv", "venv", "env", ".local", ".config"}

def build_index():
    # Ensure the directory for the DB exists before connecting
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 🧹 Clear old index for a fresh start so the new folder paths take effect
    cursor.execute("DELETE FROM files")
    
    home = os.path.expanduser("~")
    
    for folder_name in ALLOWED_ROOT_DIRS:
        base_path = os.path.join(home, folder_name)
        if not os.path.exists(base_path):
            continue
            
        print(f"Indexing {folder_name}...")
            
        for root, dirs, files in os.walk(base_path):
            # 🛑 Optimization: Skip excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for file in files:
                path = os.path.join(root, file)
                
                # Standardize extension
                ext = os.path.splitext(file)[1].lower()
                
                try:
                    mtime = os.path.getmtime(path)
                    
                    # 🚀 THE FIX: Store the full directory path (root) 
                    # instead of just the immediate parent folder name.
                    folder_full_path = root
                    
                    cursor.execute('''
                        INSERT INTO files (filename, path, ext, folder, mtime)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (file, path, ext, folder_full_path, mtime))
                except Exception:
                    # Skip files we can't access (permissions, etc.)
                    continue
                    
    conn.commit()
    conn.close()
    print("✅ Metadata Indexing Complete with Full Path support!")