import re
from datetime import datetime, timedelta

# ------------------------------------------------------------------
# Size unit map: matches KB / MB / GB (case-insensitive, with/without 's')
# ------------------------------------------------------------------
_SIZE_UNITS = {
    "byte": 1, "bytes": 1,
    "kb": 1024, "kilobyte": 1024, "kilobytes": 1024,
    "mb": 1024 ** 2, "megabyte": 1024 ** 2, "megabytes": 1024 ** 2,
    "gb": 1024 ** 3, "gigabyte": 1024 ** 3, "gigabytes": 1024 ** 3,
}

# Trigger phrases that signal "search inside file content"
_CONTENT_TRIGGERS = [
    "containing ", "with text ", "that says ", "mentioning ",
    "that has ", "with content ", "that contains ",
]


def parse_query(query: str) -> dict:
    q = query.lower()
    size_info = extract_size_filter(q)
    return {
        "name":      "",
        "ext":       extract_extension(q),
        "time":      extract_time(q),
        "content":   extract_content(query),   # preserve original case for content search
        "size_sort": size_info["size_sort"],
        "size_min":  size_info["size_min"],
        "size_max":  size_info["size_max"],
    }


def extract_extension(query: str):
    if ".tar" in query:
        return ".tar"
    if ".pdf" in query:
        return ".pdf"
    if ".py" in query or "python" in query:
        return ".py"
    if "png" in query:
        return ".png"
    if ".jpg" in query or ".jpeg" in query or "jpeg" in query:
        return ".jpg"
    if ".mp4" in query or "video" in query:
        return ".mp4"
    if ".mp3" in query or "audio" in query:
        return ".mp3"
    if ".docx" in query or "word" in query:
        return ".docx"
    if ".xlsx" in query or "excel" in query or "spreadsheet" in query:
        return ".xlsx"
    if ".zip" in query:
        return ".zip"
    if ".txt" in query or "text file" in query:
        return ".txt"
    if ".md" in query or "markdown" in query:
        return ".md"
    if ".json" in query:
        return ".json"
    if ".csv" in query:
        return ".csv"
    if ".sh" in query or "shell script" in query:
        return ".sh"
    return None


def extract_time(query: str):
    now = datetime.now()

    if "today" in query:
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return (start, now)

    if "yesterday" in query:
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start = today_start - timedelta(days=1)
        return (start, today_start)

    if "day before yesterday" in query:
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start = today_start - timedelta(days=2)
        return (start, today_start - timedelta(days=1))

    return None


def extract_content(query: str) -> str | None:
    """
    Detect a content-search trigger phrase and return the keyword(s) after it.
    Preserves original casing for accurate FTS5 matching.
    Examples:
        "python files containing import pandas" → "import pandas"
        "files mentioning GigArmor"             → "GigArmor"
    """
    q_lower = query.lower()
    for trigger in _CONTENT_TRIGGERS:
        idx = q_lower.find(trigger)
        if idx != -1:
            keyword = query[idx + len(trigger):].strip()
            return keyword if keyword else None
    return None


def extract_size_filter(query: str) -> dict:
    """
    Detect size-based intent and return size_sort / size_min / size_max.
    Examples:
        "largest file in downloads"  → size_sort="desc"
        "files over 10MB"            → size_min=10485760
        "under 500KB"                → size_max=512000
        "smallest python files"      → size_sort="asc"
    """
    size_sort = None
    size_min  = None
    size_max  = None

    q = query.lower()

    # Sort direction
    if any(w in q for w in ("largest", "biggest", "heaviest", "largest file", "biggest file")):
        size_sort = "desc"
    elif any(w in q for w in ("smallest", "lightest", "tiniest", "smallest file")):
        size_sort = "asc"

    # Size threshold — "over / more than / greater than / above / larger than X unit"
    match = re.search(
        r"(?:over|more than|greater than|above|larger than)\s+"
        r"(\d+(?:\.\d+)?)\s*(bytes?|kb|kilobytes?|mb|megabytes?|gb|gigabytes?)",
        q,
    )
    if match:
        val  = float(match.group(1))
        unit = match.group(2).rstrip("s")   # normalise plural
        size_min = int(val * _SIZE_UNITS.get(unit, 1))

    # Upper bound — "under / less than / smaller than / below X unit"
    match = re.search(
        r"(?:under|less than|smaller than|below)\s+"
        r"(\d+(?:\.\d+)?)\s*(bytes?|kb|kilobytes?|mb|megabytes?|gb|gigabytes?)",
        q,
    )
    if match:
        val  = float(match.group(1))
        unit = match.group(2).rstrip("s")
        size_max = int(val * _SIZE_UNITS.get(unit, 1))

    return {"size_sort": size_sort, "size_min": size_min, "size_max": size_max}


def extract_name(query: str):
    stopwords = {
        "today", "yesterday", "day", "before",
        "file", "files", "find", "show",
        "python", "py", ".py"
    }
    words = [w for w in query.split() if w not in stopwords]
    return words[-1] if words else ""