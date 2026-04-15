import os
from datetime import datetime
import subprocess


# folders to scan (ONLY these)
ALLOWED_ROOT_DIRS = {
    "Projects",
    "Desktop",
    "Downloads",
    "Music",
    "Videos",
    "Documents",
    "Pictures",
}

# folders to ignore inside traversal
EXCLUDE_DIRS = {
    ".cache",
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".local",
    ".config",
    "miniconda3",
}


def search_files(filters: dict, root=None):
    home = os.path.expanduser("~")

    # build allowed root paths
    root_dirs = [
        os.path.join(home, d)
        for d in ALLOWED_ROOT_DIRS
        if os.path.exists(os.path.join(home, d))
    ]

    results = []

    for base_dir in root_dirs:
        for root_dir, dirs, files in os.walk(base_dir):
            # skip unwanted dirs
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

            for file in files:
                path = os.path.join(root_dir, file)

                try:
                    mtime_ts = os.path.getmtime(path)
                    mtime = datetime.fromtimestamp(mtime_ts)
                except Exception:
                    continue

                # extension filter
                if filters["ext"] and not file.endswith(filters["ext"]):
                    continue

                # time filter
                if filters["time"]:
                    start, end = filters["time"]
                    if not (start <= mtime < end):
                        continue
                # folder filter (NEW)
                if filters.get("folder"):
                    if filters["folder"].lower() not in path.lower():
                        continue

                results.append((path, mtime_ts))

    # sort by recent
    results.sort(key=lambda x: x[1], reverse=True)

    return [r[0] for r in results]


def fast_search(filters: dict):
    query = filters["name"] or ""

    home = os.path.expanduser("~")

    try:
        result = subprocess.run(
            ["locate", query],
            capture_output=True,
            text=True
        )
    except Exception:
        return []

    paths = result.stdout.split("\n")

    results = []

    for path in paths:
        if not path or not os.path.exists(path):
            continue

        # ✅ allow only specific root dirs
        if not any(path.startswith(os.path.join(home, d)) for d in ALLOWED_ROOT_DIRS):
            continue

        # ✅ exclude unwanted dirs anywhere in path
        if any(f"/{d}/" in path for d in EXCLUDE_DIRS):
            continue

        try:
            mtime_ts = os.path.getmtime(path)
            mtime = datetime.fromtimestamp(mtime_ts)
        except Exception:
            continue

        # extension filter
        if filters["ext"] and not path.endswith(filters["ext"]):
            continue

        # time filter (range)
        if filters["time"]:
            start, end = filters["time"]
            if not (start <= mtime < end):
                continue

        # folder filter (NEW)
        if filters.get("folder"):
            if filters["folder"].lower() not in path.lower():
                continue

        results.append((path, mtime_ts))

    results.sort(key=lambda x: x[1], reverse=True)

    return [r[0] for r in results]