from datetime import datetime, timedelta


def parse_datetime_safe(dt_str):
    """Try multiple formats safely"""
    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except:
            continue

    return None


def convert_ai_to_filters(ai_data: dict):
    name = ai_data.get("name", "") or ""
    ext = ai_data.get("ext", None)
    folder = ai_data.get("folder", None)

    time_range = ai_data.get("time_range", None)
    time = None

    if time_range:
        try:
            start_str, end_str = time_range
            now = datetime.now()

            # 🔹 symbolic handling
            if start_str == "yesterday_start":
                today = now.replace(hour=0, minute=0, second=0, microsecond=0)
                start = today - timedelta(days=1)
                end = today
                time = (start, end)

            elif start_str == "today_start":
                start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end = now
                time = (start, end)

            # 🔹 NEW: actual datetime parsing
            else:
                start = parse_datetime_safe(start_str)
                end = parse_datetime_safe(end_str)

                if start and end:
                    time = (start, end)

        except Exception:
            time = None

    return {
        "name": name.lower(),
        "ext": ext,
        "time": time,
        "folder": folder,
    }