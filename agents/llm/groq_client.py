"""Groq API client — primary LLM (OpenAI-compatible endpoint)."""
import httpx

from src.config import settings

API_URL = "https://api.groq.com/openai/v1/chat/completions"
TIMEOUT = 20.0


class GroqClient:
    def __init__(self):
        self._api_key = settings.GROQ_API_KEY
        self._model = settings.GROQ_MODEL

    async def generate(self, prompt: str, system: str | None = None) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "messages": messages,
            "max_tokens": 1024,
            "temperature": 0.7,
        }

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(API_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
