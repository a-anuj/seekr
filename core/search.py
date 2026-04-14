import os
from datetime import datetime


def search_files(filters: dict, root=None):
    if root is None:
        root = os.path.expanduser("~")

    results = []

    for root_dir, dirs, files in os.walk(root):
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