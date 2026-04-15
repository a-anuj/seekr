import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.expanduser("~/.local/share/seekr/seekr.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Enable WAL for simultaneous read/write
    cursor.execute("PRAGMA journal_mode=WAL;")
    
    # Simple FTS5 table without text_content
    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS files USING fts5(
            filename, 
            path, 
            ext, 
            folder, 
            mtime UNINDEXED
        )
    ''')
    conn.commit()
    conn.close()

def search_db(filters):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # We use a subquery to handle the FTS5 'MATCH' first
    query = "SELECT path FROM files WHERE 1=1"
    params = []

    # 1. Name/Keyword Search (The FTS5 part)
    if filters.get("name") and filters["name"].strip():
        # We wrap the MATCH in a subquery to avoid the 'Context' error
        query += " AND rowid IN (SELECT rowid FROM files WHERE files MATCH ?)"
        params.append(f"{filters['name']}*") 

    # 2. Extension Search
    if filters.get("ext"):
        ext = filters["ext"] if filters["ext"].startswith(".") else f".{filters['ext']}"
        query += " AND LOWER(ext) = LOWER(?)"
        params.append(ext)
        
    # Inside search_db in core/db.py
    if filters.get("folder"):
        query += " AND folder LIKE ?"
        params.append(f"%{filters['folder']}%")

    # 4. Time Search
    if filters.get("time"):
        start, end = filters["time"]
        
        # 🚀 CONVERSION: If the router sent datetime objects, convert to timestamps
        if isinstance(start, datetime):
            start = start.timestamp()
        if isinstance(end, datetime):
            end = end.timestamp()
            
        query += " AND mtime >= ? AND mtime <= ?"
        params.extend([start, end])

    query += " ORDER BY mtime DESC LIMIT 50"
    
    try:
        cursor.execute(query, params)
        results = [row[0] for row in cursor.fetchall()]
    except Exception as e:
        print(f"SQL Error: {e}")
        results = []
    finally:
        conn.close()
    
    return results