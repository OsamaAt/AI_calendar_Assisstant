import os
import json
import openai


openai.api_key = os.getenv("OPENAI_API_KEY")


def extract_meeting_info(text: str):
    """
    Use an OpenAI chat model to extract:
      - date
      - time
      - title
    from the user's text. Returns a dict with those keys.
    """
    if not openai.api_key:
        # Fail safe if API key is missing
        return {
            "date": None,
            "time": None,
            "title": None,
        }

    system_prompt = (
        "You are a helpful assistant that extracts meeting information from text. "
        "Given a user's sentence, return a JSON object with exactly these keys: "
        '"date", "time", and "title". '
        'If something is missing or unclear, use null for that field. '
        "Use an ISO-like date format when possible (e.g. 2024-05-10) and a 24-hour "
        'time format like "14:30". Do not include any text outside the JSON.'
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            temperature=0,
        )

        content = response.choices[0].message["content"]

        # Try to parse the model's reply as JSON
        return json.loads(content)
    except Exception:
        # Fallback if anything goes wrong (API error, JSON parse error, etc.)
        return {
            "date": None,
            "time": None,
            "title": None,
        }