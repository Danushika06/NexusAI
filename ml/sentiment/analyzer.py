"""Groq-based sentiment analyzer — replaces local DistilBERT.

Calls Groq LLM to score distress in [0, 1] where 1 = maximum distress.
Falls back to 0.5 (neutral) on any API error to avoid blocking risk scoring.
"""
import httpx

from ml.sentiment.preprocessor import clean_text
from src.config import settings

API_URL = "https://api.groq.com/openai/v1/chat/completions"
TIMEOUT = 10.0

_SYSTEM = (
    "You are a mental health text classifier. "
    "Given a student's message, output ONLY a single decimal number between 0.0 and 1.0 "
    "representing the distress level. "
    "0.0 = completely positive/neutral. 1.0 = maximum distress/crisis. "
    "Output the number only, no explanation."
)


class SentimentAnalyzer:
    async def analyze(self, text: str) -> float:
        cleaned = clean_text(text)
        if not cleaned:
            return 0.0

        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": cleaned},
            ],
            "max_tokens": 10,
            "temperature": 0.0,
        }

        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                response = await client.post(API_URL, json=payload, headers=headers)
                response.raise_for_status()
                raw = response.json()["choices"][0]["message"]["content"].strip()
                score = float(raw)
                return max(0.0, min(1.0, score))
        except Exception:
            return 0.5  # neutral fallback — don't block risk scoring
