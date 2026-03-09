import os
import json
import logging
from pathlib import Path

logger = logging.getLogger("college_chatbot.ai")

try:
    from google import genai
    from google.genai import types
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False
    logger.warning("google-genai not installed")

# Load colleges data once for context injection
_BASE = Path(__file__).parent.parent
_colleges_cache = None

def _get_colleges_summary():
    global _colleges_cache
    if _colleges_cache is not None:
        return _colleges_cache
    try:
        with open(_BASE / "data" / "colleges.json", encoding="utf-8") as f:
            colleges = json.load(f)
        lines = []
        for c in colleges[:60]:  # limit context size
            name = c.get("name", "")
            loc = c.get("location") or c.get("city") or c.get("state") or ""
            courses = ", ".join(c.get("courses") or []) if isinstance(c.get("courses"), list) else str(c.get("courses", ""))
            fee = c.get("fee") or c.get("fees") or c.get("annual_fee") or ""
            lines.append(f"- {name} | {loc} | Courses: {courses} | Fee: {fee}")
        _colleges_cache = "\n".join(lines)
    except Exception as e:
        logger.warning("Could not load colleges for context: %s", e)
        _colleges_cache = "(college data unavailable)"
    return _colleges_cache


SYSTEM_PROMPT = """You are EduGuide AI, a friendly and knowledgeable college admissions assistant for Indian students.
You help students find the right college based on their interests, budget, location, and course preferences.

You have access to the following college data:
{colleges}

Guidelines:
- Answer clearly and concisely
- If asked about specific colleges, fees, or courses, use the data above
- If a question is outside your knowledge, say so honestly
- Support English, Hindi, and Malayalam queries
- Format lists with bullet points for readability
- Keep responses under 200 words unless more detail is needed
"""


def get_chat_response(user_message: str, language: str = "en") -> str:
    """
    Call Gemini API and return a response string.
    Falls back to a helpful error message if the API is unavailable.
    """
    if not _GENAI_AVAILABLE:
        return "⚠️ AI module not available. Please install google-genai."

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or api_key == "your_gemini_api_key_here":
        return "⚠️ Gemini API key not configured. Please add your key to the .env file."

    try:
        client = genai.Client(api_key=api_key)
        system_instruction = SYSTEM_PROMPT.format(colleges=_get_colleges_summary())
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                max_output_tokens=400,
                temperature=0.7,
            )
        )
        return response.text.strip()
    except Exception as e:
        logger.exception("Gemini API error: %s", e)
        return f"⚠️ AI error: {str(e)}"
