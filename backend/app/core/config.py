
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_CHAT_MODEL = os.getenv(
    "GROQ_CHAT_MODEL",
    "llama-3.3-70b-versatile"
)
GROQ_STT_MODEL = os.getenv(
    "GROQ_STT_MODEL",
    "whisper-large-v3-turbo"
)

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
ELEVENLABS_MODEL = os.getenv(
    "ELEVENLABS_MODEL",
    "eleven_flash_v2_5"
)
