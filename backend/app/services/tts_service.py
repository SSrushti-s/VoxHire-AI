
import httpx

from app.core.config import (
    ELEVENLABS_API_KEY,
    ELEVENLABS_VOICE_ID,
    ELEVENLABS_MODEL
)


async def generate_speech(text: str) -> bytes:
    """
    Converts AI-generated text into speech.
    """

    url = (
        f"https://api.elevenlabs.io/v1/text-to-speech/"
        f"{ELEVENLABS_VOICE_ID}"
        "?output_format=mp3_44100_128"
    )

    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "text": text,
        "model_id": ELEVENLABS_MODEL
    }

    async with httpx.AsyncClient(timeout=60.0) as http:
        response = await http.post(
            url,
            headers=headers,
            json=payload
        )

        response.raise_for_status()

        return response.content
