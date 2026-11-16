
from groq import AsyncGroq
from app.core.config import GROQ_API_KEY, GROQ_STT_MODEL

client = AsyncGroq(api_key=GROQ_API_KEY)


async def transcribe_audio(audio_bytes: bytes, filename: str):
    """
    Converts recorded audio into text using Whisper.
    """

    result = await client.audio.transcriptions.create(
        file=(filename, audio_bytes),
        model=GROQ_STT_MODEL,
        language="en",
        response_format="json",
        temperature=0.0
    )

    return result.text.strip()
