"""LLMRouter — tries Groq first, falls back to Ollama (gpt-oss)."""
import asyncio
import time

from .groq_client import GroqClient
from .ollama_client import OllamaClient

GROQ_TIMEOUT = 20.0
OLLAMA_TIMEOUT = 15.0          # More generous now that it's the fallback
CIRCUIT_BREAK_SECONDS = 300    # Skip a failed provider for 5 min


class LLMRouter:
    def __init__(self):
        self._groq = GroqClient()
        self._ollama = OllamaClient()
        self._groq_failed_at: float = 0.0
        self._ollama_failed_at: float = 0.0

    async def generate(self, prompt: str, system: str | None = None) -> str:
        # --- Primary: Groq ---
        if time.time() - self._groq_failed_at > CIRCUIT_BREAK_SECONDS:
            try:
                return await asyncio.wait_for(
                    self._groq.generate(prompt, system),
                    timeout=GROQ_TIMEOUT,
                )
            except Exception:
                self._groq_failed_at = time.time()

        # --- Fallback: Ollama (gpt-oss) ---
        if time.time() - self._ollama_failed_at > CIRCUIT_BREAK_SECONDS:
            try:
                return await asyncio.wait_for(
                    self._ollama.generate(prompt, system),
                    timeout=OLLAMA_TIMEOUT,
                )
            except Exception:
                self._ollama_failed_at = time.time()

        return (
            "I'm here to support you. Our AI service is temporarily "
            "experiencing connectivity issues, but your message has been "
            "received. Please try again in a moment, or reach out to your "
            "counselor directly if you need immediate support."
        )


_router: LLMRouter | None = None


def get_llm_router() -> LLMRouter:
    global _router
    if _router is None:
        _router = LLMRouter()
    return _router
