from groq import Groq
from dotenv import load_dotenv
import os
import json

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found in environment variables")

client = Groq(api_key=api_key)

def ai_parse(query: str):
    prompt = f"""
            Convert this user query into JSON filters.

            Query: "{query}"

            Return ONLY JSON with:
            - name (string)
            - ext (string or null)
            - time_range (["start", "end"] or null)
            - folder (string or null)

            Example - 1:
            Query: "python files yesterday"
            Output:
            {{
            "name": "",
            "ext": ".py",
            "time_range": ["yesterday_start", "today_start"],
            "folder": null
            }}

            Example - 2:
            Query: "python files last week"
            Output:
            {{
            "name": "",
            "ext": ".py",
            "time_range": ["last week start date", "last week end date"],
            "folder": null

            For this example 2 , replace the time_range with actual values.
            }}

            """

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        answer = json.loads(response.choices[0].message.content)
        print(answer)
        return answer
    except:
        return None