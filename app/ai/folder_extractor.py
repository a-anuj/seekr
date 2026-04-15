from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

from groq import Groq
import os

def get_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("API key not set")
    return Groq(api_key=api_key)

def ai_extract_folder(query: str):
    prompt = f"""
    Extract ONLY the folder keyword.

    Query: "{query}"

    STRICT RULES:
    - Return ONLY the keyword (1 word max)
    - DO NOT explain
    - DO NOT include reasoning
    - DO NOT include <think>
    - DO NOT include sentences
    - If nothing → return empty string ""

    Examples:
    "python files in abc folder" → "abc"
    "find report pdf in xyz" → xyz
    "that parser file I edited in the gigArmour" → gigArmour

    Output ONLY the keyword.
    """
    client = get_client()
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}]
    )

    result = response.choices[0].message.content.strip().lower()
    print("Folder: ",result)

    # remove think
    if "<think>" in result:
        result = result.split("</think>")[-1].strip()

    # 🔥 FIX: remove quotes completely
    result = result.replace('"', '').replace("'", '').strip()

    # final cleanup
    if result in ["", "none", "null"]:
        return ""

    return result.split()[0]