import os
from datetime import datetime


EXCLUDE_DIRS = {
    ".cache",
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".local",
}

def search_files(filters: dict, root=None):
    if root is None:
        root = os.path.expanduser("~")

    results = []

    for root_dir, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            path = os.path.join(root_dir, file)

            # extension filter
            if filters["ext"] and not file.endswith(filters["ext"]):
                continue

            # name filter
            if filters["name"] and filters["name"] not in file.lower():
                continue

            # time filter
            if filters["time"]:
                mtime = datetime.fromtimestamp(os.path.getmtime(path))
                if mtime < filters["time"]:
                    continue

            results.append((path, os.path.getmtime(path)))

    # sort by recent
    results.sort(key=lambda x: x[1], reverse=True)

    return [r[0] for r in results]