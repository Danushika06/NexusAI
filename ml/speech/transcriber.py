"""Groq Whisper API — async audio-to-text transcription."""
import httpx

from src.config import settings

API_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
MODEL = "whisper-large-v3-turbo"
TIMEOUT = 30.0


class Transcriber:
    async def transcribe(self, audio_bytes: bytes, filename: str = "audio.wav") -> str:
        headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
        files = {"file": (filename, audio_bytes, "audio/wav")}
        data = {"model": MODEL}

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                API_URL, headers=headers, files=files, data=data
            )
            response.raise_for_status()
            return response.json().get("text", "").strip()
