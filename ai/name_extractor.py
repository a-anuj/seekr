from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def ai_extract_name(query: str):
    prompt = f"""
    Extract ONLY the filename keyword.

    Query: "{query}"

    STRICT RULES:
    - Return ONLY the keyword (1 word max)
    - DO NOT explain
    - DO NOT include reasoning
    - DO NOT include <think>
    - DO NOT include sentences
    - If nothing → return empty string ""

    Examples:
    "python files today" → ""
    "find report pdf" → report
    "that parser file I edited" → parser

    Output ONLY the keyword.
    """

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}]
    )

    result = response.choices[0].message.content.strip().lower()
    print(result)

    # remove think
    if "<think>" in result:
        result = result.split("</think>")[-1].strip()

    # 🔥 FIX: remove quotes completely
    result = result.replace('"', '').replace("'", '').strip()

    # final cleanup
    if result in ["", "none", "null"]:
        return ""

    return result.split()[0]