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
    return None


def extract_time(query: str):
    now = datetime.now()

    if "today" in query:
        return now
    if "yesterday" in query:
        return now - timedelta(days=1)
    if "day before yesterday" in query:
        return now - timedelta(days=2)

    return None


def extract_name(query: str):
    words = query.split()
    return words[-1] if words else ""