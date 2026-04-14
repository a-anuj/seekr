from datetime import datetime, timedelta

def parse_query(query: str) -> dict:
    query = query.lower()

    return {
        "name": extract_name(query),
        "ext": extract_extension(query),
        "time": extract_time(query)
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
    return None


def extract_time(query: str):
    now = datetime.now()

    if "today" in query:
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
        return (start, end)

    if "yesterday" in query:
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start = today_start - timedelta(days=1)
        end = today_start
        return (start, end)

    if "day before yesterday" in query:
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start = today_start - timedelta(days=2)
        end = today_start - timedelta(days=1)
        return (start, end)

    return None

def extract_name(query: str):
    stopwords = {
        "today", "yesterday", "day", "before",
        "file", "files", "find", "show",
        "python", "py", ".py"   # 👈 ADD THIS
    }

    words = [w for w in query.split() if w not in stopwords]

    return words[-1] if words else ""