from core.parser import parse_query
from ai.name_extractor import ai_extract_name
from ai.parser_ai import ai_parse
from ai.utils import convert_ai_to_filters

print("ROUTER OPENED")

def is_strong(filters):
    score = 0

    if filters.get("time"):
        score += 2
    if filters.get("ext"):
        score += 1   # weaker than time
    if filters.get("folder"):
        score += 2
    if filters.get("name"):
        score += 2   # strong if valid

    return score >= 3

def clean_filters(filters):
    if filters.get("name") in ["", '""', "none", "null"]:
        filters["name"] = ""

    return filters

def get_filters(query: str):
    # 🔹 Step 1: rule-based
    filters = parse_query(query)
    filters = clean_filters(filters)

    # 🔹 Step 2: ALWAYS improve name using AI
    try:
        ai_name = ai_extract_name(query)
        print("Getting through this block ")
        print("AI NAme : ",ai_name)
        if ai_name:
            filters["name"] = ai_name or ""
            print("AI NAME:", ai_name)
    except Exception as e:
        print(e)  # fail silently

    # 🔹 Step 3: check confidence
    if is_strong(filters):
        return filters

    # 🔹 Step 4: fallback to full AI
    try:
        ai_data = ai_parse(query)

        if ai_data:
            ai_filters = convert_ai_to_filters(ai_data)
            print("AI - Filters : ",ai_filters)

            if is_strong(ai_filters):
                print("AI - Filters : ",ai_filters)
                return ai_filters
    except:
        pass

    # 🔹 fallback
    print("Local - Filters : ",filters)
    return filters